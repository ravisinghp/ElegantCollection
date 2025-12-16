"use client"

import { Loader2 } from "lucide-react"
import { motion } from "framer-motion"

interface FullScreenLoaderProps {
    message?: string
}

export default function FullScreenLoader({ message = "" }: FullScreenLoaderProps) {
    return (
        <div className="fixed inset-0 w-screen h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 via-gray-800 to-black z-50">
            <motion.div
                className="flex flex-col items-center space-y-6"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.4, ease: "easeOut" }}
            >
                {/* Glowing Loader Icon */}
                <motion.div
                    className="relative"
                    animate={{ rotate: 360 }}
                    transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
                >
                    <div className="absolute -inset-3 rounded-full bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 opacity-30 blur-xl animate-pulse" />
                    <Loader2 className="h-14 w-14 text-white drop-shadow-lg opacity-80" />
                </motion.div>

                {/* App Title / Branding */}
                <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent tracking-wide">
                    Loading...
                </h1>

                {/* Loader Message */}
                <motion.p
                    className="text-lg text-gray-300 font-medium"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.5, duration: 0.8, repeat: Infinity, repeatType: "reverse" }}
                >
                    {message}
                </motion.p>
            </motion.div>
        </div>
    )
}
