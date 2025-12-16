"use server"

import { z } from "zod"
import { v4 as uuidv4 } from "uuid"
import axiosClient from "@/app/api/axiosClient";
import { cookies } from "next/headers";

// Define schema for user creation
const createUserSchema = z.object({
  name: z.string().min(1, "Name is required"),
  email: z.string().min(1, "Email is required").email("Invalid email address"),
  role_id: z.number({ required_error: "Role is required" }),
  department: z.string().optional(),
  password: z.string().optional(),
})

//define schema for keyword creation
const createKeywordSchema = z.object({
  keyword_text: z.string().min(1, "keyword name is required"),
  org_id: z.string().min(1, "Org ID is required"),
  created_by: z.string().min(1, "Created by is required"), // 👈 Add this line
})


// #User Listing On Admin Dashboard Page
export async function getUsers() {
  try {
    const response = await axiosClient.get("/admin/users");
    return response.data;  // axios automatically parses JSON
  } catch (err: any) {
    throw new Error(
      `Failed to fetch users: ${err.response?.status} ${err.response?.statusText}`
    );
  }
}


// listing the keywords on admin screen 
export async function getKeywords() {
  try {
    const response = await axiosClient.get("/admin/keywords");
    return response.data;  // axios automatically parses JSON
  } catch (err: any) {
    throw new Error(
      `Failed to fetch keywords: ${err.response?.status} ${err.response?.statusText}`
    );
  }
}

// Listing the dropdown of roles from DB On UI
export async function getRoles() {
  try {
    const response = await axiosClient.get("/admin/roles")
    return response.data
  } catch (err: any) {
    throw new Error(
      `Failed to fetch roles: ${err.response?.status} ${err.response?.statusText}`
    )
  }
}


//Listing the card data above on Admin Dashboard at the On Load process
export async function getDashboardCardData(from: string, to: string, userId: number) {
  try {
    const response = await axiosClient.get("/admin/dashboardCardData", {
      params: {
        from_date: from,
        to_date: to,
        userId: userId, // only if backend supports this param
      },
    });

    return response.data;
  } catch (err: any) {
    throw new Error(
      `failed to fetch data : ${err.response?.status} ${err.response?.statusText}`
    );
  }
}


export async function getUserDashboardCardData(from: string, to: string, userId: number) {
  try {

    const response = await axiosClient.get(`/userdash/userDashboardCardData`, {
      params: {
        from_date: from,
        to_date: to,
        userId: userId, // only if backend supports this param
      },
      withCredentials: true
    });

    return response.data;
  } catch (err: any) {
    throw new Error(
      `Failed to fetch data: ${err.response?.status} ${err.response?.statusText}`
    );
  }
}




export async function createUserAndMailCredentials(prevState: any, formData: FormData) {

  // const user_id = localStorage.getItem("userid") ||  sessionStorage.getItem("userid")
  // const org_id = localStorage.getItem("orgid") || sessionStorage.getItem("orgid")

  const cookieStore = await cookies();
  const user_id = cookieStore.get("userid")?.value;
  const org_id = cookieStore.get("orgid")?.value;
  const created_by = cookieStore.get("userid")?.value; // 👈 Admin ID here
  const data = {
    // name: formData.get("name"),
    // email: formData.get("email"),
    // role: formData.get("role"),
    // department: formData.get("department"),
    user_name: formData.get("name"),
    mail_id: formData.get("email"),
    // password: Math.random().toString(36).substring(2, 10), // temporary password
    // org_name: formData.get("department"),
    org_id: org_id,
    user_id: user_id,
    role_id: Number(formData.get("role_id")),
    folder_name: "default_folder",
    password: formData.get("password"),
    created_by: created_by,

  }

  const validatedFields = createUserSchema.safeParse({
    name: data.user_name,
    email: data.mail_id,
    role_id: data.role_id,
    // department: data.org_name,
    org_id: data.org_id,
    password: data.password,
    created_by: data.created_by,
  })

  if (!validatedFields.success) {
    return {
      success: false,
      message: "Validation failed",
      errors: validatedFields.error.flatten().fieldErrors,
    }
  }

  try {
    //called FastAPI backend with cookies enabled
    const response = await axiosClient.post("/admin/createUser", data, {
      withCredentials: true,  // this will send cookies for this request only
    });

    return {
      success: true,
      message: `User ${response.data.user_name} created successfully.`,
    };
  } catch (err: any) {
    console.error("Error creating user:", err.response?.data || err.message);
    return {
      success: false,
      message: `Failed to create user: ${err.response?.data?.detail || err.message}`,
    };
  }
}

export async function createKeywords(prevState: any, formData: FormData) {
  const cookieStore = await cookies();
  const org_id = cookieStore.get("orgid")?.value;
  const created_by = cookieStore.get("userid")?.value; // 👈 Admin ID here

  const data = {
    keyword_text: formData.get("keyword"),
    org_id: org_id,
    created_by: created_by,  // 👈 Add this to data

  }

  const validatedFields = createKeywordSchema.safeParse({
    keyword_text: data.keyword_text,
    org_id: data.org_id,
    created_by: data.created_by, // 👈 Validate this as well

  })

  if (!validatedFields.success) {
    return {
      success: false,
      message: "Validation failed",
      errors: validatedFields.error.flatten().fieldErrors,
    }
  }

  try {
    //called FastAPI backend
    const response = await axiosClient.post("/admin/createKeyword", data)

    return {
      success: true,
      message: `Keyword ${response.data.keyword_text} created successfully.`,
    }
  }

  catch (err: any) {
    console.error("Error creating Keyword:", err.response?.data || err.message)
    return {
      success: false,
      message: `Failed to create keyword: ${err.response?.data?.detail || err.message}`,
    }
  }

}

//   const { name, email, role, department } = validatedFields.data

//   // Simulate user creation in DB
//   const newUserId = uuidv4()
//   const temporaryPassword = Math.random().toString(36).substring(2, 10) // Simple temporary password

//   console.log(`Simulating user creation:
//     ID: ${newUserId}
//     Name: ${name}
//     Email: ${email}
//     Role: ${role}
//     Department: ${department || "N/A"}
//     Temporary Password: ${temporaryPassword}
//   `)

//   // Simulate sending email with credentials
//   console.log(`Simulating email to ${email} with temporary password: ${temporaryPassword}`)

//   // In a real app, you would:
//   // 1. Hash the temporaryPassword before storing it
//   // 2. Store the new user in your 'users' table
//   // 3. Use a transactional email service (e.g., SendGrid, Mailgun) to send the actual email

//   return {
//     success: true,
//     message: `User ${name} created successfully. Credentials simulated to be emailed to ${email}.`,
//   }
// }

// Mock function to simulate fetching user data (e.g., for current user's email connection status)
export async function getUserEmailConnectionStatus(userId: string) {
  // In a real application, this would fetch from your database
  // For now, let's simulate a connected user
  if (userId === "mock-user-id") {
    return {
      emailConnected: true,
      emailProvider: "google",
      lastScanDate: new Date().toISOString(),
    }
  }
  return {
    emailConnected: false,
    emailProvider: null,
    lastScanDate: null,
  }




}
