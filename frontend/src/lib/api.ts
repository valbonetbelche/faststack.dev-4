import axios from "axios";

// Base URL for the backend API
const PUBLIC_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";
const PRIVATE_BASE_URL = process.env.NEXT_PRIVATE_API_BASE_URL || "http://backend:8000/api/v1";
// Create an Axios instance
const publicApiClient = axios.create({
  baseURL: PUBLIC_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

const privateApiClient = axios.create({
  baseURL: PRIVATE_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add a response interceptor to handle errors globally
publicApiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Handle specific error statuses
      switch (error.response.status) {
        case 401:
          // Redirect to login or refresh token
          console.error("Unauthorized: Please log in.");
          break;
        case 404:
          console.error("Resource not found.");
          break;
        case 500:
          console.error("Server error. Please try again later.");
          break;
        default:
          console.error("An error occurred:", error.message);
      }
    } else if (error.request) {
      console.error("No response received:", error.request);
    } else {
      console.error("Request setup error:", error.message);
    }
    return Promise.reject(error);
  }
);

// Add a response interceptor to handle errors globally
privateApiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Handle specific error statuses
      switch (error.response.status) {
        case 401:
          // Redirect to login or refresh token
          console.error("Unauthorized: Please log in.");
          break;
        case 404:
          console.error("Resource not found.");
          break;
        case 500:
          console.error("Server error. Please try again later.");
          break;
        default:
          console.error("An error occurred:", error.message);
      }
    } else if (error.request) {
      console.error("No response received:", error.request);
    } else {
      console.error("Request setup error:", error.message);
    }
    return Promise.reject(error);
  }
);

// API methods
export const publicApi = {
  // Billing Service
  getPlans: async (token: string) => {
    const response = await publicApiClient.get("/billing/plans/", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  },

  createCheckoutSession: async (data: { plan_id: number }, token: string) => {
    const response = await publicApiClient.post("/billing/subscription/checkout", data, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  },

  getCurrentSubscription: async (token: string) => {
    const response = await publicApiClient.get("/billing/subscription/current/", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  },

  getStripeBillingUrl: async (token: string) => {
    const response = await publicApiClient.get("/billing/subscription/billing-portal", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data.billing_portal_url;
  },

  // Auth Service
  login: async (credentials: { email: string; password: string }) => {
    const response = await publicApiClient.post("/auth/login/", credentials);
    return response.data;
  },

  // User Service
  getUserProfile: async (userId: string, token: string) => {
    const response = await publicApiClient.get(`/user/profile/${userId}/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  },
};


export const privateApi = {
}