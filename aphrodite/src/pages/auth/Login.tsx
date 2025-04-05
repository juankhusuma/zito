import React from "react"
import supabase from "../../common/supabase"
import { useNavigate } from "react-router"

export default function Login() {
    const [email, setEmail] = React.useState("")
    const [password, setPassword] = React.useState("")
    const navigate = useNavigate()

    return (
        <div className="flex items-center justify-center h-screen">
            <form className="flex flex-col w-1/2 border border-black p-5 font-mono" onSubmit={async (e) => {
                e.preventDefault()
                const { error } = await supabase.auth.signInWithPassword({
                    email,
                    password
                })
                if (error) {
                    console.error("Login error:", error)
                    return
                }
                navigate("/")
            }}>
                <a className="text-sm underline text-blue-600 mb-2" href="/register">
                    Don't have an account? Register here
                </a>
                <input className="my-2 p-2 border border-black" type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
                <input className="my-2 p-2 border border-black" type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
                <button className="border-black border p-2 bg-gray-200 cursor-pointer" type="submit">Login</button>
            </form>
        </div>
    )
}