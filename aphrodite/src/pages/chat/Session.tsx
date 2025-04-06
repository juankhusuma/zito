import React, { useEffect } from "react";
import { useNavigate, useParams } from "react-router";
import { useAuth } from "../../hoc/AuthProvider";
import supabase from "../../common/supabase";

interface Chat {
    id: string;
    role: "user" | "assistant";
    content: string;
    created_at: string;
    user_uid: string;
    session_uid: string;
    is_loading: boolean;
}

export default function Session() {
    const navigate = useNavigate()
    const { sessionId } = useParams()
    const { user, loading } = useAuth()
    const [chats, setChats] = React.useState<Chat[]>([])
    const [prompt, setPrompt] = React.useState("")

    useEffect(() => {
        if (!loading && !user) {
            console.log("User not found, redirecting to login")
            navigate("/login")
        }
    }, [user, loading, navigate])

    useEffect(() => {
        if (!user) return
        supabase.from("chat").select("*").eq("session_uid", sessionId).then(({ data, error }) => {
            if (error) {
                console.error("Error fetching chats:", error)
                return
            }
            setChats(data)
            console.log("Fetched chats:", data)
        })

        supabase.channel("chat")
            .on("postgres_changes", { event: "INSERT", schema: "public", table: "chat", filter: `session_uid=eq.${sessionId}` }, (payload) => {
                console.log("New chat:", payload)
                setChats((prev) => [...prev, payload.new as Chat])
            })
            .on("postgres_changes", { event: "UPDATE", schema: "public", table: "chat", filter: `session_uid=eq.${sessionId}` }, (payload) => {
                console.log("Updated chat:", payload)
                setChats((prev) => prev.map((chat) => chat.id === payload.new.id ? payload.new as Chat : chat))
            })
            .subscribe((status) => {
                console.log("Subscription status:", status)
            })
    }, [user])

    return (
        <div className='font-mono p-5 flex flex-col justify-center items-center'>
            <h1 className='font-bold mb-10'>Chat Session</h1>
            <table className="w-1/2">
                <thead>
                    <tr>
                        <th></th>
                        <th></th>
                    </tr>
                </thead>
                <tbody>
                    {chats.sort((a, b) => (
                        new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
                    )).map((chat) => (
                        chat.role === "user" ? (
                            <tr key={chat.id}>
                                <td className='p-2 max-w-1/2 w-1/2 text-wrap'></td>
                                <td className='p-2 max-w-1/2 w-1/2 text-wrap text-end'><span className="font-bold">user:</span> {chat.content}</td>
                            </tr>
                        ) : (
                            <tr key={chat.id}>
                                <td className='p-2 max-w-1/2 w-1/2 text-wrap'><span className="font-bold">assistant:</span> {chat.is_loading ? "loading..." : chat.content}</td>
                                <td className='p-2 max-w-1/2 w-1/2 text-wrap'></td>
                            </tr>
                        )
                    ))}
                </tbody>
            </table>
            <form className="w-1/2 flex fixed bottom-20" onSubmit={async (e) => {
                e.preventDefault()
                if (!user) return
                const { error } = await supabase.from("chat").insert({
                    role: "user",
                    content: prompt,
                    session_uid: sessionId
                })
                if (error) {
                    console.error("Error inserting chat:", error)
                    return
                }
                const { data } = await supabase.auth.getSession()
                if (!data.session) {
                    console.error("No session found")
                    return
                }
                const res = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/chat`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        session_uid: sessionId,
                        user_uid: user.id,
                        access_token: data.session?.access_token,
                        refresh_token: data.session?.refresh_token,
                        messages: [...chats.map((chat) => ({
                            content: chat.content,
                            role: chat.role,
                            timestamp: chat.created_at
                        })), {
                            content: prompt,
                            role: "user",
                            timestamp: new Date().toISOString()
                        }]
                    })
                })
                const json = await res.json()
                console.log("Response:", json)
                setPrompt("")
            }}>
                <input className="border flex-1 border-black p-2" type="text" placeholder="Type your message..." value={prompt} onChange={(e) => setPrompt(e.target.value)} />
                <button className="bg-gray-200 cursor-pointer p-2 border-black border" type="submit">Send</button>
            </form>
        </div>
    )
}