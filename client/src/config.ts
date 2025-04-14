// Configuration for API endpoints

const config = {
  // Environment-based API URL selection
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL || "https://e0xv6c1woa.execute-api.us-east-1.amazonaws.com/api"
};

export default config;
