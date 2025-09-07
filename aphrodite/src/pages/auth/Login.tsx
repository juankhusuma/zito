import React, { useMemo } from "react"
import supabase from "../../common/supabase"
import { useLocation, useNavigate } from "react-router"
import PrimaryButton from "@/components/button"
import { Icon } from "@iconify/react/dist/iconify.js"
import { useAuth } from "@/hoc/AuthProvider"

export default function Login() {
    const [email, setEmail] = React.useState("")
    const { search } = useLocation();
    const [password, setPassword] = React.useState("")
    const [reveal, setReveal] = React.useState<boolean>(false)
    const { loading, setLoading } = useAuth()
    const [isError, setIsError] = React.useState<boolean>(false)
    const [errorMessage, setErrorMessage] = React.useState<string>("")
    const query = useMemo(() => new URLSearchParams(search), [search]);

    const navigate = useNavigate()

    return (
        <div className="flex h-screen">
            {/* Left column - Image */}
            <div className="hidden lg:block lg:w-1/2 relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-r from-[#192f59]/90 to-[#192f59]/80 z-10"></div>
                <img
                    src="/hukum.jpg"
                    alt="Legal background"
                    className="absolute inset-0 h-full w-full object-cover object-center"
                />
                <div className="absolute inset-0 z-20 flex flex-col justify-center items-center text-white p-12">
                    <div className="max-w-md">
                        <h1 className="text-4xl font-bold mb-6">Legal Generative-AI Search</h1>
                        <p className="text-lg text-blue-100">
                            Akses database hukum Indonesia dengan mudah melalui kecerdasan buatan yang responsif dan akurat.
                        </p>
                    </div>
                </div>
            </div>

            {/* Right column - Login form */}
            <div className="w-full lg:w-1/2 flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
                <div className="max-w-md w-full space-y-8">
                    <div className="text-center">
                        <h2 className="text-3xl font-extrabold text-gray-900">Selamat Datang</h2>
                        <p className="mt-2 text-sm text-gray-600">
                            Belum memiliki akun? {' '}
                            <a href="/register" className="font-medium text-[#192f59] hover:text-[#0d1e3f] transition-colors">
                                Daftar
                            </a>
                        </p>
                        {isError && (
                            <div className="mt-4 bg-red-50 border-l-4 border-red-500 p-4">
                                <div className="flex items-center">
                                    <div className="flex-shrink-0">
                                        <svg className="h-5 w-5 text-red-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                                            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                                        </svg>
                                    </div>
                                    <div className="ml-3">
                                        <p className="text-sm text-red-700">{errorMessage}</p>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>

                    <form className="mt-8 space-y-6" onSubmit={async (e) => {
                        e.preventDefault()
                        setLoading(true)
                        const res = await supabase.auth.signInWithPassword({
                            email,
                            password
                        })
                        if (res.error) {
                            setLoading(false)
                            setIsError(true)
                            setErrorMessage(res.error.message)
                            return
                        }
                        setLoading(false)
                        console.log(query.get("next"))
                        navigate(query.get("next") || "/")
                    }}>
                        <div className="rounded-md -space-y-px">
                            <div className="mb-4">
                                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                                    Email
                                </label>
                                <input
                                    id="email"
                                    name="email"
                                    type="email"
                                    autoComplete="email"
                                    required
                                    value={email}
                                    onChange={e => setEmail(e.target.value)}
                                    className="appearance-none relative block w-full px-3 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-[#192f59] focus:border-[#192f59] focus:z-10 sm:text-sm"
                                    placeholder="Masukan email Anda"
                                />
                            </div>
                            <div className="mb-2">
                                <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                                    Password
                                </label>
                                <div className="relative">
                                    <input
                                        id="password"
                                        name="password"
                                        type={reveal ? "text" : "password"}
                                        autoComplete="current-password"
                                        required
                                        value={password}
                                        onChange={e => setPassword(e.target.value)}
                                        className="appearance-none relative block w-full px-3 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-[#192f59] focus:border-[#192f59] focus:z-10 sm:text-sm"
                                        placeholder="Masukan password Anda"
                                    />
                                    <div
                                        className="cursor-pointer absolute right-3 top-3 text-gray-500 hover:text-gray-700 transition-colors"
                                        onClick={() => setReveal(prev => !prev)}
                                    >
                                        <Icon
                                            icon={reveal ? "mdi:eye-off" : "mdi:eye"}
                                            style={{ fontSize: '20px' }}
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div>
                            <PrimaryButton
                                isLoading={loading}
                                type="submit"
                                className="w-full py-3 bg-[#192f59] hover:bg-[#0d1e3f] text-center flex justify-center transition-colors shadow-sm"
                            >
                                <span className="mr-2">Masuk</span>
                                {!loading && (
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                        <path fillRule="evenodd" d="M10.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L12.586 11H5a1 1 0 110-2h7.586l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
                                    </svg>
                                )}
                            </PrimaryButton>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    )
}

