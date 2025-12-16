"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { CheckCircle, AlertCircle, Loader2 } from "lucide-react";
import axiosClient from "@/app/api/axiosClient";

export default function TermsAndConditions() {
  const [isChecked, setIsChecked] = useState(false);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleCheckboxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setIsChecked(e.target.checked);
  };

  // const handleProceed = async () => {
  //   if (!isChecked) return

  //   setLoading(true)

  //   try {
  //     // Call your backend to get the token
  //     const response = await axiosClient.get("/auth/login",{
  //            params: {provider: localStorage.getItem("provider")}})
  //     if (response.data?.auth_url) {
  //       window.location.replace(response.data.auth_url)
  //      // router.replace(response.data.auth_url)
  //     } else {
  //       console.error("Neither token nor auth_url found in response:", response.data)
  //     }

  //     // Get the token from backend response
  //     const { token } = response.data

  //     // Store the token in localStorage
  //     localStorage.setItem("token", token)

  //     // You can also store other data if your backend returns it
  //     if (response.data.userData) {
  //       localStorage.setItem("userData", JSON.stringify(response.data.userData))
  //     }

  //     // Redirect to user dashboard after successful token storage
  //     router.replace("/dashboard/user")

  //   } catch (error) {
  //     console.error("Error accepting terms:", error)
  //     alert("Failed to proceed. Please try again.")
  //   } finally {
  //     setLoading(false)
  //   }
  // }

  const handleProceed = async () => {
    if (!isChecked) return;

    setLoading(true);

    try {
      const userId =
        localStorage.getItem("userid") || sessionStorage.getItem("userid");
      const roleId =
        localStorage.getItem("roleid") || sessionStorage.getItem("roleid");
      const orgId =
        localStorage.getItem("orgid") || sessionStorage.getItem("orgid");

      if (!userId || !roleId || !orgId) {
        alert("User info missing. Please login again.");
        router.replace("/login");
        return;
      }

      // Accept terms first
      await axiosClient.post(
        `/userdash/update_term_condition_flag?user_id=${userId}&role_id=${roleId}&org_id=${orgId}`
      );
//       await axiosClient.post("/userdash/acceptTerms", {
//   user_id: userId,
//   role_id: roleId,
//   org_id: orgId
// });
// localStorage.setItem("term_condition_flag", "1");
      const provider =
  localStorage.getItem("provider") ||
  sessionStorage.getItem("provider");
      localStorage.setItem("term_condition_flag", "1");
//  const provider = localStorage.getItem("provider") || "Outlook";     
      const response = await axiosClient.get("/auth/login", {
      params: { provider },
    });

    if (response.data?.auth_url) {
      window.location.replace(response.data.auth_url);
    } else {
      console.error("No auth_url returned:", response.data);
      alert("Unable to proceed with Outlook login.");
    }
    } catch (error) {
      console.error("Error proceeding:", error);
      alert("Failed to proceed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center  p-6">
      <div className="bg-white shadow-lg rounded-2xl p-8 max-w-2xl w-full">
        <h1 className="text-2xl font-bold mb-4 text-gray-800">
          Terms & Conditions
        </h1>

        <div className="h-64 overflow-y-auto border p-4 rounded-lg mb-6 bg-gray-50  dark:bg-gray-800 text-sm text-gray-700 dark:text-gray-300">
          <p>
            Welcome to our application. By accessing or using this app, you
            agree to comply with the following terms and conditions. Please read
            carefully before proceeding.
          </p>
          <br />
          <p>
            1. You must use this application responsibly and in compliance with
            all applicable laws and regulations.
          </p>
          <p>
            2. We are not responsible for any misuse of the information provided
            through this app.
          </p>
          <p>
            3. Your personal information will be handled in accordance with our
            Privacy Policy.
          </p>
          <p>
            4. We reserve the right to update these terms at any time without
            prior notice.
          </p>
          <p>
            5. By continuing, you acknowledge that you have read, understood,
            and agreed to these terms.
          </p>
        </div>

        {/* Checkbox */}
        <div className="flex items-center mb-6">
          <input
            id="accept"
            type="checkbox"
            checked={isChecked}
            onChange={handleCheckboxChange}
            className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
          />
          <label htmlFor="accept" className="ml-2 block text-gray-700">
            I agree to the Terms & Conditions
          </label>
        </div>

        {/* Proceed Button */}
        <Button
          onClick={handleProceed}
          disabled={!isChecked || loading}
          className={`w-full py-3 px-4 rounded-xl text-white font-semibold transition ${
            isChecked && !loading
              ? "bg-primary  text-primary-foreground hover:bg-primary/90aria-invalid:border-destructive aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40"
              : "bg-gray-400 cursor-not-allowed"
          }`}
        >
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Processing...
            </>
          ) : (
            <>
              <CheckCircle className="h-4 w-4 mr-2" />
              Proceed to Dashboard
            </>
          )}
        </Button>

        {/* Warning */}
        <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-center">
            <AlertCircle className="h-4 w-4 text-yellow-600 mr-2" />
            <p className="text-sm text-yellow-800">
              You must accept the terms and conditions to continue using the
              application.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
