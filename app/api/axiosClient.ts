import axios from "axios";

// Create Axios instance with base URL
const axiosClient = axios.create({
  baseURL: "http://localhost:8080", // FastAPI backend URL
  headers: {
    "Content-Type": "application/json",
  },
});

export default axiosClient;
