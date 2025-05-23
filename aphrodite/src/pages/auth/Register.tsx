import React from "react"
import supabase from "../../common/supabase"
import { useNavigate } from "react-router"
import { Icon } from "@iconify/react/dist/iconify.js"
import PrimaryButton from "@/components/button"

export default function Register() {
    const [email, setEmail] = React.useState("")
    const [password, setPassword] = React.useState("")
    const navigate = useNavigate()
    const [reveal, setReveal] = React.useState<boolean>(false)
    const [loading, setLoading] = React.useState<boolean>(false)
    const [isError, setIsError] = React.useState<boolean>(false)
    const [errorMessage, setErrorMessage] = React.useState<string>("")

    return (

        <form className="flex justify-center items-center h-full mb-[10rem]" onSubmit={async (e) => {
            e.preventDefault()
            setLoading(true)
            const res = await supabase.auth.signUp({
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
            navigate("/login")
        }}>
            <div className="bg-[#FFFFFF] py-10 px-6 flex flex-col items-center rounded-sm border shadow-xl w-[600px] translate-y-12">
                <div className="flex flex-col items-center">
                    <h1 className="text-2xl font-bold">
                        Daftar
                    </h1>
                    <h1 className="mb-6 text-sm">
                        Sudah memiliki akun? <a className="text-blue-600 underline font-semibold" href="/login">Masuk</a>
                    </h1>
                    {isError && <p className="text-red-500 text-xs my-3 text-start">{errorMessage}</p>}
                </div>
                <div className="w-full">
                    <div className="flex flex-col my-2">
                        <span className="mb-1 font-semibold">Email</span>
                        <div className="">
                            <input
                                type="text"
                                placeholder="Masukan email Anda"
                                value={email}
                                onChange={e => setEmail(e.target.value)}
                                className={"p-2 rounded-sm text-sm border-[1px] border-gray border-solid w-full"}
                            />
                        </div>
                    </div>
                    <div className="flex flex-col my-2">
                        <span className="mb-1 font-semibold">Password</span>
                        <div className="relative">
                            <input
                                type={reveal ? "text" : "password"}
                                placeholder="Masukan password Anda"
                                value={password}
                                onChange={e => setPassword(e.target.value)}
                                className="p-2 rounded-sm text-sm border-[1px] border-gray border-solid w-full"
                            />
                            <div
                                className="cursor-pointer absolute right-3 top-2"
                                onClick={() => {
                                    setReveal(prev => !prev)
                                }}
                            >
                                <Icon
                                    icon={reveal ? "mdi:eye-off" : "mdi:eye"}
                                    style={{ fontSize: '20px' }}
                                />
                            </div>
                        </div>
                    </div>
                    <PrimaryButton
                        isLoading={loading}
                        type="submit"
                        className="mt-5 w-full text-center flex justify-center">
                        Masuk
                    </PrimaryButton>
                </div>
            </div>
        </form>
    )
}