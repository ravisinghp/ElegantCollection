"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ArrowRight, UserCog, Zap, Loader2 } from "lucide-react";
import axiosClient from "@/app/api/axiosClient";
import { useToast } from "@/hooks/use-toast";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { useRouter } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import Cookies from "js-cookie";
// import { useSearchParams } from "react-router-dom";
import { useSearchParams } from "next/navigation";
import { usePathname } from "next/navigation";
const getUserContext = () => {
  let userId =
    sessionStorage.getItem("userid") || localStorage.getItem("userid");
  let orgid = sessionStorage.getItem("orgid") || localStorage.getItem("orgid");
  let roleId =
    sessionStorage.getItem("roleid") || localStorage.getItem("roleid");
  return { userId, orgid, roleId };
};
//  validation schema
const loginSchema = z.object({
  email: z.string().email("Please enter a valid email"),
  password: z.string().min(6, "Password must be at least 6 characters"),
  rememberMe: z.boolean().optional(),
});

const forgotPasswordSchema = z.object({
  email: z.string().email("Please enter a valid email"),
});

const resetPasswordSchema = z
  .object({
    newPassword: z
      .string()
      .min(6, "New Password must be at least 6 characters"),
    confirmPassword: z
      .string()
      .min(6, "Confirm Password must be at least 6 characters"),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });
type LoginFormData = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const [provider, setProvider] = useState<string>("");
  //   const searchParams = useSearchParams();
  //   const token = searchParams.get("token");
  //   const reset = searchParams.get("reset") === "true";
  const [step, setStep] = useState<"login" | "forgot" | "reset">("login");

 useEffect(() => {
  // Add a fake history entry so Back button doesn't leave the site
  window.history.pushState(null, "", window.location.href);
//   const handlePopState = () => {
//     setStep("login");
// // Push state again so that the next Back press still stays inside the app
//     window.history.pushState(null, "", window.location.href);
//   };
const handlePopState = () => {
    setStep("login");
   resetLoginForm();  //calls react-hook-form reset()
  resetResetForm();  //calls reset form’s reset()
  
    window.history.pushState(null, "", window.location.href);
};
  window.addEventListener("popstate", handlePopState);
  // Cleanup listener on unmount
  return () => window.removeEventListener("popstate", handlePopState);
}, []);


  const [userId, setUserId] = useState<number | null>(null);
  const [orgId, setOrgId] = useState<number>(1); // or get from login/session if dynamic

  const [token, setToken] = useState<string | null>(null);
  const [reset, setReset] = useState<boolean>(false);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const tokenParam = params.get("token");
      const resetParam = params.get("reset") === "true";

      setToken(tokenParam);
      setReset(resetParam);
    }
  }, []);

  useEffect(() => {
    if (reset) {
      setStep("reset"); //show reset section
      setVerified(true);
    }
  }, [reset]);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset: resetLoginForm,
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: { rememberMe: false },
  });

  const {
    register: registerForgot,
    handleSubmit: handleSubmitForgot,
    formState: { errors: forgotErrors },
     reset: resetForgotForm, 
  } = useForm<{ email: string }>({
    resolver: zodResolver(forgotPasswordSchema),
  });

  const [verified, setVerified] = useState(false);
  const handleForgotSubmit = async (data: { email: string }) => {
    setLoading(true); // Start loader
    try {
      //const { orgid } = getUserContext();
      
      const response = await axiosClient.post("/users/forgotPassword", {

        email: data.email,
        //org_id: orgid,
      });

      toast({
        title: "Success",
        description: response.data?.message || "Reset link sent to your email",
      });

      //Optionally, navigate user to a "Check your email" page
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.response?.data?.detail || "Email id not found",
        variant: "destructive",
      });
    }
    finally {
    setLoading(false); // Stop loader
  }
  };

  const {
    register: registerReset,
    handleSubmit: handleSubmitReset,
    formState: { errors: resetErrors },
    reset: resetResetForm,
  } = useForm<{ newPassword: string; confirmPassword: string }>({
    resolver: zodResolver(resetPasswordSchema),
  });

  const handleResetSubmit = async (data: {
    newPassword: string;
    confirmPassword: string;
  }) => {
    if (!token) {
      toast({
        title: "Error",
        description: "Invalid or missing reset token",
        variant: "destructive",
      });
      return;
    }
    setLoading(true); // Start loader

    try {
      const response = await axiosClient.post("/users/resetPassword", {
        token,
        new_password: data.newPassword,
        confirm_password: data.confirmPassword,
      });

      toast({
        title: "Success",
        description: response.data?.message || "Password reset successful",
      });

      resetResetForm();
      // Navigate to login page
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.response?.data?.detail || "Failed to reset password",
        variant: "destructive",
      });
    }
     finally {
    setLoading(false); // Stop loader
  }
  };

  const onSubmit = async (data: LoginFormData) => {
    setLoading(true);
    try {
      const response = await axiosClient.post("/users/login", {
        user: {
          email: data.email,
          password: data.password,
        },
      });

      const {
        userid,
        orgid,
        roleid,
        token,
        rolename,
        username,
        term_condition_flag,
        provider,
      } = response.data;
      const email = data.email.toLowerCase();

      // const provider = response.data.provider; //backend value

      //detect provider
      // if (email.endsWith("gmail.com")) {
      //   setProvider("Gmail");
      //   localStorage.setItem("provider", "Gmail");
      //   Cookies.set("provider", "Gmail", { expires: 30 });
      // } else {
      //   setProvider("Outlook");
      //   localStorage.setItem("provider", "Outlook");
      //   Cookies.set("provider", "Outlook", { expires: 30 });
      // }

      // const selectedProvider = provider || "google";
      // setProvider(selectedProvider);
      // localStorage.setItem("provider", selectedProvider);
      // Cookies.set("provider", selectedProvider, { expires: 30 });
      

      // persist session
      if (data.rememberMe) {
        localStorage.setItem("userid", userid);
        localStorage.setItem("orgid", orgid);
        localStorage.setItem("roleid", roleid);
        localStorage.setItem("rolename", rolename);
        localStorage.setItem("token", token);
        localStorage.setItem("username", username);
        Cookies.set("userid", userid, { expires: 30 });
        Cookies.set("orgid", orgid, { expires: 30 });
        Cookies.set("roleid", roleid, { expires: 30 });
        Cookies.set("rolename", rolename, { expires: 30 });
        Cookies.set("token", token, { expires: 30 });
        Cookies.set("username", username, { expires: 30 });
      } else {
        sessionStorage.setItem("userid", userid);
        sessionStorage.setItem("orgid", orgid);
        sessionStorage.setItem("roleid", roleid);
        sessionStorage.setItem("rolename", rolename);
        sessionStorage.setItem("token", token);
        sessionStorage.setItem("username", username);
        Cookies.set("userid", userid);
        Cookies.set("orgid", orgid);
        Cookies.set("roleid", roleid);
        Cookies.set("rolename", rolename);
        Cookies.set("token", token);
        Cookies.set("username", username);
      }

      // stop loader first
      setLoading(false);

      // role-based routing with replace (no back history)
      if (roleid === 1 || rolename === "Admin") {
        Cookies.set("insideApp", "true", { path: "/", expires: 1 });
        router.replace("/dashboard/admin"); //  replace removes history
        toast({
          title: "Login Successful",
          description: `Welcome back, ${username || "Admin"}!`,
        });
      } else if (rolename === "User" || roleid === 2) {
        Cookies.set("insideApp", "true", { path: "/", expires: 1 });

        if (term_condition_flag === 1) {
          //Already accepted terms - go directly to provider login
          //const provider = email.endsWith("gmail.com") ? "google" : "outlook";

          // const response = await axiosClient.get("/auth/login", {
          //   params: { provider },
          // });

          if (!provider) {
            toast({
              title: "Provider Missing",
              description:
                "Your account has no provider assigned. Please contact admin.",
              variant: "destructive",
            });
            return;
          }

          setProvider(provider);
          localStorage.setItem("provider", provider);
          sessionStorage.setItem("provider", provider);
          Cookies.set("provider", provider, { expires: 30 });

          const responseAuth = await axiosClient.get("/auth/login", {
            params: { provider },
          });

          //const selectedProvider = Cookies.get("provider") || provider || "google";

          // const response = await axiosClient.get("/auth/login", {
          //   params: { provider },
          // });

          if (responseAuth.data?.auth_url) {
            window.location.replace(responseAuth.data.auth_url);
          } else {
            console.error("No auth_url returned:", responseAuth.data);
            toast({
              title: "Login Error",
              description:
                "Unable to get authorization link for your provider.",
              variant: "destructive",
            });
          }
        } else {
          // Redirect to terms page if not accepted
          router.replace(
            `/login/terms?userid=${encodeURIComponent(
              userid
            )}&roleid=${encodeURIComponent(roleid)}&orgid=${encodeURIComponent(
              orgid
            )}`
          );
          
          setProvider(provider);
          localStorage.setItem("provider", provider);
          sessionStorage.setItem("provider", provider);
          Cookies.set("provider", provider, { expires: 30 });
        }

        //   if (response.data?.auth_url) {
        //     window.location.replace(response.data.auth_url);
        //   } else {
        //     console.error("No auth_url returned:", response.data);
        //     alert("Unable to proceed with Outlook login.");
        //   }
        // } else {
        //   //Not acceptedgo to terms page
        //   router.replace(
        //     `/login/terms?userid=${encodeURIComponent(userid)}
        //         &roleid=${encodeURIComponent(roleid)}
        //         &orgid=${encodeURIComponent(orgid)}`
        //   );
        // }

        toast({
          title: "Login Successful",
          description: `Welcome back, ${username || "User"}!`,
        });
      }
    } catch (error: any) {
      setLoading(false);
      toast({
        title: "Error",
        description: error.response?.data?.errors?.[0] || "Login failed",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/30 backdrop-blur-[2px] z-50">
          <div className="flex flex-col items-center space-y-4 text-white">
            <Loader2 className="h-10 w-10 animate-spin" />
            <p className="text-xl font-semibold">Signing in...</p>
          </div>
        </div>
      )}

      <div className="w-full max-w-sm">
        {/* Logo/Brand Section */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-12 h-12 bg-primary rounded-2xl mb-4 shadow-lg">
            <Zap className="h-8 w-8 text-primary-foreground" />
          </div>
          <h1 className=" font-heading font-bold text-foreground mb-2 text-2xl">
            R&D Estimator
          </h1>
          <p className="text-muted-foreground">
            Intelligent effort tracking for research teams
          </p>
        </div>

        <Card className="shadow-lg">
          <CardHeader className="text-center">
            <CardTitle className="text-xl font-heading font-bold">
              Sign in to your account
            </CardTitle>
          </CardHeader>

          <CardContent className="space-y-6">
            <>
              {step === "login" && (
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                  <Label className="text-sm font-medium text-foreground flex flex-col items-start">
                    <span>Email</span>
                    <Input
                      type="email"
                      placeholder="Enter your email"
                      className="mt-1 h-[2.2rem] placeholder:text-sm"
                      {...register("email")}
                    />
                    {errors.email && (
                      <p className="text-red-500 text-sm mt-1">
                        {errors.email.message}
                      </p>
                    )}
                  </Label>

                  <Label className="text-sm font-medium text-foreground flex flex-col items-start">
                    <span>Password</span>
                    <Input
                      type="password"
                      placeholder="Enter Password"
                      className="mt-1 h-[2.2rem] placeholder:text-sm"
                      {...register("password")}
                    />
                    {errors.password && (
                      <p className="text-red-500 text-sm mt-1">
                        {errors.password.message}
                      </p>
                    )}
                  </Label>

                  <div className="flex items-center justify-between hidden">
                    <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        {...register("rememberMe")}
                        className="w-4 h-4"
                      />
                      <span className="text-sm text-gray-500 dark:text-gray-300">
                        Remember me
                      </span>
                    </label>
                  </div>
                  {/* Provider selection
<div className="flex justify-center gap-6 mt-2">
  <label className="flex items-center space-x-2">
    <input
      type="radio"
      name="provider"
      value="google"
      checked={provider === "google"}
      onChange={() => setProvider("google")}
    />
    <span>Gmail</span>
  </label>

  <label className="flex items-center space-x-2">
    <input
      type="radio"
      name="provider"
      value="outlook"
      checked={provider === "outlook"}
      onChange={() => setProvider("outlook")}
    />
    <span>Outlook</span>
  </label>
</div> */}

                  <Button
                    type="submit"
                    className="w-full py-4 text-lg shadow-md hover:shadow-lg transition-all duration-300"
                  >
                    {/* <UserCog className="h-6 w-6 mr-3" /> */}
                    {loading ? "Logging in..." : "Login"}
                    <ArrowRight className=" h-5 w-5" />
                  </Button>

                  <p
                   onClick={() => {
                      resetLoginForm();     //clear login form
                      resetForgotForm();    //clear forgot form too
                      resetResetForm(); 
                      setStep("forgot");    // show forgot screen
                    }}
                    className="cursor-pointer text-sm text-gray-500 hover:underline flex justify-center"
                  >
                    Forgot your password?
                  </p>
                </form>
              )}

              {step === "forgot" && (
                <form
                  onSubmit={handleSubmitForgot(handleForgotSubmit)}
                  className="space-y-4"
                >
                  <Label>Email</Label>
                  <Input
                    type="email"
                    {...registerForgot("email")}
                    placeholder="Enter your email"
                    className="mt-1 h-[2.2rem] placeholder:text-sm"
                  />
                  {forgotErrors.email && (
                    <p className="text-red-500 text-sm mt-1">
                      {forgotErrors.email.message}
                    </p>
                  )}

                   <Button type="submit" disabled={loading} className={`w-full py-4 text-lg shadow-md transition-all duration-300 ${
                        loading ? "cursor-not-allowed opacity-70" : "hover:shadow-lg"
                      }`}
                    >
                      {loading ? (
                        <div className="flex items-center justify-center">
                          <svg
                            className="animate-spin h-5 w-5 text-white mr-2"
                            xmlns="http://www.w3.org/2000/svg"
                            fill="none"
                            viewBox="0 0 24 24"
                          ><circle   className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path
                              className="opacity-75"
                              fill="currentColor"
                              d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                            ></path>
                          </svg>
                          Sending...
                        </div>
                      ) : (
                        "Verify Email"
                      )}
                    </Button>

                  <p
                    onClick={() => setStep("login")}
                    className="cursor-pointer text-sm text-gray-500 hover:underline"
                  >
                    Back to login
                  </p>
                </form>
              )}
             
              {/* RESET */}
              {step === "reset" && (
                <form
                  onSubmit={handleSubmitReset(handleResetSubmit)}
                  className="space-y-4"
                >
                  <Label>New Password</Label>
                  <Input
                    type="password"
                    {...registerReset("newPassword")}
                    disabled={!verified}
                    placeholder="Enter New Password"
                    className="mt-1 h-[2.2rem] placeholder:text-sm"
                  />
                  {resetErrors.newPassword && (
                    <p className="text-red-500 text-sm mt-1">
                      {resetErrors.newPassword.message}
                    </p>
                  )}

                  <Label>Confirm Password</Label>
                  <Input
                    type="password"
                    {...registerReset("confirmPassword")}
                    disabled={!verified}
                    placeholder="Confirm New Password"
                    className="mt-1 h-[2.2rem] placeholder:text-sm"
                  />
                  {resetErrors.confirmPassword && (
                    <p className="text-red-500 text-sm mt-1">
                      {resetErrors.confirmPassword.message}
                    </p>
                  )}

                   <Button type="submit" disabled={loading} className={`w-full py-4 text-lg shadow-md transition-all duration-300 ${
                        loading ? "cursor-not-allowed opacity-70" : "hover:shadow-lg"
                      }`}
                    >
                      {loading ? (
                        <div className="flex items-center justify-center">
                          <svg
                            className="animate-spin h-5 w-5 text-white mr-2"
                            xmlns="http://www.w3.org/2000/svg"
                            fill="none"
                            viewBox="0 0 24 24"
                          ><circle   className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path
                              className="opacity-75"
                              fill="currentColor"
                              d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                            ></path>
                          </svg>
                          Sending...
                        </div>
                      ) : (
                        "Reset & Login"
                      )}
                    </Button>
                  <p
                    onClick={() => setStep("login")}
                    className="cursor-pointer text-sm text-gray-500 hover:underline"
                  >
                    Back to login
                  </p>
                </form>
              )}
            </>

            {/* <div className="pt-4 border-t">
              <p className="text-center text-sm text-muted-foreground">
                By signing in, you agree to our{" "}
                <Link
                  href="#"
                  className="text-primary hover:underline transition-colors"
                >
                  Terms of Service
                </Link>{" "}
                and{" "}
                <Link
                  href="#"
                  className="text-primary hover:underline transition-colors"
                >
                  Privacy Policy
                </Link>
                .
              </p>
            </div> */}
          </CardContent>
        </Card>

        <div className="text-center mt-8">
          {/* <p className="text-muted-foreground text-sm">
            Powered by AI-driven research analytics
          </p> */}
        </div>
      </div>
    </div>
  );
}
