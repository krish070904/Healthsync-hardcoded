    # prototype_meal_planner.py
    import pandas as pd
    import random
    from math import floor

    # ---- simple Mifflin-St Jeor BMR -> calories
    def mifflin_calories(sex, weight_kg, height_cm, age, activity_factor=1.2):
        if sex.lower() in ("m", "male"):
            bmr = 10*weight_kg + 6.25*height_cm - 5*age + 5
        else:
            bmr = 10*weight_kg + 6.25*height_cm - 5*age - 161
        return int(bmr * activity_factor)

    # ---- greedy meal generator using local CSV
    def load_foods(csv_path="data/food_sample.csv"):
        df = pd.read_csv(csv_path)
        # compute calories per gram
        df['cal_per_g'] = df['calories_per_100g'] / 100.0
        return df

    def filter_allergies(df, allergies):
        if not allergies:
            return df
        low = [a.strip().lower() for a in allergies]
        # filter where any allergy string appears in tags or name
        mask = df.apply(lambda r: not any(a in str(r['tags']).lower() or a in str(r['name']).lower() for a in low), axis=1)
        return df[mask].reset_index(drop=True)

    def generate_meal_for_target(df, target_cal, max_items=4):
        picked = []
        remaining = target_cal
        # sort foods by protein density (simple heuristic)
        df['protein_density'] = df['protein_g_per_100g'] / df['calories_per_100g'].replace(0,1)
        candidates = df.sort_values('protein_density', ascending=False).to_dict('records')
        idx = 0
        while remaining > 40 and idx < len(candidates) and len(picked) < max_items:
            food = candidates[idx]
            # choose serving grams so that item contributes ~25%-50% of remaining if possible
            desired = min(food['serving_g'], max(20, floor(remaining * 0.4 / food['cal_per_g'])))
            calories = desired * food['cal_per_g']
            picked.append({"name": food['name'], "grams": int(desired), "calories": int(calories)})
            remaining -= calories
            idx += 1
        # fill with smallest calorie items if remaining is still big
        if remaining > 40:
            for f in reversed(candidates):
                if len(picked) >= max_items: break
                desired = min(f['serving_g'], max(20, floor(remaining / f['cal_per_g'])))
                calories = desired * f['cal_per_g']
                picked.append({"name": f['name'], "grams": int(desired), "calories": int(calories)})
                remaining -= calories
                if remaining <= 40: break
        total = sum(p['calories'] for p in picked)
        return picked, total

    def make_daily_plan(user, df):
        daily_cal = mifflin_calories(user['sex'], user['weight_kg'], user['height_cm'], user['age'], user.get('activity_factor',1.2))
        # distribution: breakfast 25%, lunch 40%, dinner 30%, snack 5%
        dist = {'breakfast':0.25, 'lunch':0.4, 'dinner':0.3, 'snack':0.05}
        plan = {}
        for meal, frac in dist.items():
            target = int(daily_cal * frac)
            items, total = generate_meal_for_target(df, target)
            plan[meal] = {"target_calories": target, "items": items, "total_calories": total}
        plan['daily_calories_target'] = daily_cal
        plan['daily_total_planned'] = sum(plan[m]['total_calories'] for m in plan if m != 'daily_calories_target' and m != 'daily_total_planned')
        return plan

    if __name__ == "__main__":
        # example user profile (edit these values)
        user = {
            "name": "Test User",
            "sex": "male",
            "age": 25,
            "height_cm": 175,
            "weight_kg": 70,
            "activity_factor": 1.3,
            "allergies": ["peanut"]  # example
        }
        df = load_foods("data/food_sample.csv")
        df = filter_allergies(df, user.get('allergies', []))
        plan = make_daily_plan(user, df)
        import json
        print(json.dumps(plan, indent=2))
