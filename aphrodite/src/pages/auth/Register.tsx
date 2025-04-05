import React from "react"
import supabase from "../../common/supabase"
import { useNavigate } from "react-router"

export default function Register() {
    const [email, setEmail] = React.useState("")
    const [password, setPassword] = React.useState("")
    const navigate = useNavigate()

    return (
        <div className="flex items-center justify-center h-screen">
            <form className="p-5 flex-col flex font-mono w-1/2 border border-black" action="" onSubmit={async (e) => {
                e.preventDefault()
                await supabase.auth.signUp({
                    email,
                    password
                })
                navigate("/login")
            }}>
                <input className="border border-black my-2 p-2" type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
                <input className="border border-black my-2 p-2" type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
                <button className="bg-gray-200 cursor-pointer p-2 border-black border" type="submit">Register</button>
            </form>
        </div>
    )
}