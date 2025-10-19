/**
 * HealthSync Authentication Module
 * Handles user registration, login, and session management
 */

// Use localStorage for storing encrypted user data
const AUTH_TOKEN_KEY = 'healthsync_auth_token';
const USER_DATA_KEY = 'healthsync_user_data';

// Simple encryption function for basic security
function encrypt(text, secretKey) {
    // In a production environment, use a proper encryption library
    // This is a simple XOR encryption for demonstration
    const result = [];
    for (let i = 0; i < text.length; i++) {
        result.push(String.fromCharCode(text.charCodeAt(i) ^ secretKey.charCodeAt(i % secretKey.length)));
    }
    return btoa(result.join('')); // Base64 encode the result
}

// Simple decryption function
function decrypt(encoded, secretKey) {
    try {
        const text = atob(encoded); // Base64 decode
        const result = [];
        for (let i = 0; i < text.length; i++) {
            result.push(String.fromCharCode(text.charCodeAt(i) ^ secretKey.charCodeAt(i % secretKey.length)));
        }
        return result.join('');
    } catch (e) {
        console.error('Decryption failed:', e);
        return null;
    }
}

// Generate a random token
function generateToken() {
    return Math.random().toString(36).substring(2, 15) + 
           Math.random().toString(36).substring(2, 15) + 
           Date.now().toString(36);
}

// Secret key for encryption (in production, this would be securely stored)
const SECRET_KEY = 'healthsync_secure_key_2023';

// Authentication class
class Auth {
    constructor() {
        this.isAuthenticated = false;
        this.currentUser = null;
        this.checkAuth();
    }

    // Check if user is authenticated
    checkAuth() {
        const token = localStorage.getItem(AUTH_TOKEN_KEY);
        const userData = localStorage.getItem(USER_DATA_KEY);
        
        if (token && userData) {
            try {
                this.currentUser = JSON.parse(decrypt(userData, SECRET_KEY));
                this.isAuthenticated = true;
                return true;
            } catch (e) {
                console.error('Authentication check failed:', e);
                this.logout(); // Clear invalid data
            }
        }
        
        return false;
    }
    
    // Get all users from localStorage
    getAllUsers() {
        const usersData = localStorage.getItem('healthsync_users');
        if (!usersData) {
            return [];
        }
        
        try {
            return JSON.parse(decrypt(usersData, SECRET_KEY));
        } catch (e) {
            console.error('Failed to get users:', e);
            return [];
        }
    }

    // Register a new user
    async register(fullName, email, password) {
        try {
            // Call the server's registration endpoint
            const response = await fetch('/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: fullName,
                    email,
                    password,
                }),
            });

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Registration failed');
            }

            // Store pending verification email in sessionStorage
            sessionStorage.setItem('pending_verification_email', email);
            
            // Show alert to user
            alert('Registration successful! Please check your email for verification link.');
            
            // Redirect to verify page
            window.location.href = 'verify.html';
            return true;
        } catch (error) {
            console.error('Registration error:', error);
            return false;
        }
    }
    
    async verifyEmail(email, token) {
        try {
            const response = await fetch('/auth/verify', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email,
                    token,
                }),
            });

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Verification failed');
            }

            // Store auth token and user data
            this.storeAuthToken(data.token);
            this.storeUserData(data.user);
            
            // Clear pending verification
            sessionStorage.removeItem('pending_verification_email');

            return true;
        } catch (error) {
            console.error('Verification error:', error);
            return false;
        }
    }
    
    // Send verification email (simulated)
    sendVerificationEmail(email, token) {
        console.log(`Verification email sent to ${email} with token: ${token}`);
        // In a real implementation, this would send an actual email
        // For demo purposes, we'll create a verification link that can be clicked
        const verificationLink = `verify.html?email=${encodeURIComponent(email)}&token=${encodeURIComponent(token)}`;
        
        // Display verification link in console for testing
        console.log(`Verification link: ${window.location.origin}/html_pages/${verificationLink}`);
        
        // Show alert with instructions instead of auto-redirecting
        setTimeout(() => {
            alert(`Verification email sent to ${email}. Please check the console (F12) for the verification link.`);
            // Redirect to login page
            window.location.href = 'login.html';
        }, 1000);
    }
    
    // Verify user email
    verifyEmail(email, token) {
        return new Promise((resolve, reject) => {
            const users = this.getAllUsers();
            const userIndex = users.findIndex(user => user.email === email && user.verificationToken === token);
            
            if (userIndex === -1) {
                return reject(new Error('Invalid verification link'));
            }
            
            const user = users[userIndex];
            
            // Check if verification link has expired
            if (new Date(user.verificationExpiry) < new Date()) {
                return reject(new Error('Verification link has expired'));
            }
            
            // Mark user as verified
            user.verified = true;
            user.verificationToken = null;
            user.verificationExpiry = null;
            
            // Update user in storage
            users[userIndex] = user;
            localStorage.setItem('healthsync_users', encrypt(JSON.stringify(users), SECRET_KEY));
            
            // Log verification (simulating database update)
            console.log('USER VERIFIED IN DATABASE:');
            console.log({
                email: user.email,
                verified: true,
                verifiedAt: new Date().toISOString()
            });
            
            // Auto login after verification
            this.login(email, decrypt(user.password, SECRET_KEY))
                .then(() => resolve(this.currentUser))
                .catch(reject);
        });
    }

    // Login user
    async login(email, password) {
        try {
            // Call the server's login endpoint
            const response = await fetch('/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email,
                    password,
                }),
            });

            const data = await response.json();

            if (!data.success) {
                // Check if verification is required
                if (data.verificationRequired) {
                    // Store email for verification page
                    sessionStorage.setItem('pending_verification_email', email);
                    alert('Your email is not verified. Please check your email for verification link.');
                    window.location.href = 'verify.html';
                    return false;
                }
                throw new Error(data.error || 'Login failed');
            }

            // Store auth token and user data
            localStorage.setItem(AUTH_TOKEN_KEY, data.token);
            localStorage.setItem(USER_DATA_KEY, encrypt(JSON.stringify(data.user), SECRET_KEY));
            
            // Update state
            this.currentUser = data.user;
            this.isAuthenticated = true;

            // Redirect to index page (with navbar)
            window.location.href = 'index.html';
            return true;
        } catch (error) {
            console.error('Login error:', error);
            return false;
        }
    }

    // Logout user
    logout() {
        localStorage.removeItem(AUTH_TOKEN_KEY);
        localStorage.removeItem(USER_DATA_KEY);
        this.isAuthenticated = false;
        this.currentUser = null;
    }
    
    // Check if user is authenticated
    isAuthenticated() {
        return this.checkAuth();
    }
    
    // Get current user
    getCurrentUser() {
        return this.currentUser;
    }
}

// Create global auth instance
const auth = new Auth();

// Helper function to redirect if authenticated
function redirectIfAuthenticated() {
    if (auth.checkAuth()) {
        window.location.href = 'index.html';
    }
}

// Helper function to redirect if not authenticated
function redirectIfNotAuthenticated() {
    if (!auth.checkAuth()) {
        window.location.href = 'registration.html';
    }
}