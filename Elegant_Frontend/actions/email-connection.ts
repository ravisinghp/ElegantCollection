"use server"

import { redirect } from "next/navigation"
import { v4 as uuidv4 } from "uuid"

// In a real application, these would be environment variables
const GOOGLE_CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID"
const MICROSOFT_CLIENT_ID = "YOUR_MICROSOFT_CLIENT_ID"
const REDIRECT_URI = "http://localhost:3000/dashboard/user" // Or a specific OAuth callback route

export async function initiateOAuth(provider: "google" | "microsoft") {
  let authUrl = ""
  const state = uuidv4() // CSRF protection

  if (provider === "google") {
    authUrl = `https://accounts.google.com/o/oauth2/v2/auth?client_id=${GOOGLE_CLIENT_ID}&redirect_uri=${REDIRECT_URI}&response_type=code&scope=https://www.googleapis.com/auth/gmail.readonly&access_type=offline&prompt=consent&state=${state}`
  } else if (provider === "microsoft") {
    authUrl = `https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id=${MICROSOFT_CLIENT_ID}&response_type=code&redirect_uri=${REDIRECT_URI}&scope=Mail.Read&state=${state}`
  } else {
    throw new Error("Unsupported OAuth provider")
  }

  // In a real app, you'd store 'state' in a cookie or session for verification later
  console.log(`Initiating OAuth for ${provider}. Redirecting to: ${authUrl}`)
  redirect(authUrl) // This will redirect the user's browser
}

export async function handleOAuthCallback(code: string, provider: "google" | "microsoft", userId: string) {
  // In a real application, you would exchange the 'code' for an access token and refresh token
  // using a server-side request to the OAuth provider's token endpoint.
  // You would then encrypt and store the refresh token in your database associated with the user.

  console.log(`Simulating OAuth callback for ${provider} with code: ${code}`)
  console.log(`Simulating token exchange and saving for user: ${userId}`)

  const simulatedAccessToken = `simulated_access_token_${uuidv4()}`
  const simulatedRefreshToken = `simulated_refresh_token_${uuidv4()}`

  // Update user's email connection status in DB
  // This would involve updating the 'users' table:
  // - email_connected = TRUE
  // - email_provider = provider
  // - email_token_encrypted = encrypted_refresh_token (NEVER store plain access tokens)
  // - last_scan_date = CURRENT_TIMESTAMP (or null, depending on first scan logic)

  console.log(`User ${userId} email connection status updated to connected with ${provider}.`)

  return {
    success: true,
    message: `Successfully connected with ${provider}. Your emails will now be scanned.`,
    provider,
  }
}
