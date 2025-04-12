import React, { useEffect, useRef } from "react";
import { useNavigate, useParams } from "react-router";
import { useAuth } from "../../hoc/AuthProvider";
import supabase from "../../common/supabase";
import { PromptInput, PromptInputAction, PromptInputActions, PromptInputTextarea } from "@/components/ui/prompt-input";
import { Button } from "@/components/ui/button";
import { ArrowUp, Square } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import ChatBubble from "@/components/chat/bubble";

interface Chat {
    id: string;
    role: "user" | "assistant";
    content: string;
    created_at: string;
    user_uid: string;
    session_uid: string;
    state: "done" | "loading" | "error" | "generating";
}

export default function Session() {
    const navigate = useNavigate()
    const { sessionId } = useParams()
    const { user, loading } = useAuth()
    const [chats, setChats] = React.useState<Chat[]>([])
    const [isLoading, setIsLoading] = React.useState(false)
    const [prompt, setPrompt] = React.useState("")
    const scrollAreaRef = useRef<HTMLDivElement>(null)

    const scrollToBottom = () => {
        if (scrollAreaRef.current) {
            const scrollContainer = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]');
            if (scrollContainer) {
                scrollContainer.scrollTop = scrollContainer.scrollHeight;
            }
        }
    }

    useEffect(() => {
        setIsLoading(chats.some((chat) => chat.state === "loading"))
    }, [chats])

    useEffect(() => {
        if (!loading && !user) {
            console.log("User not found, redirecting to login")
            navigate("/login")
        }
    }, [user, loading, navigate])

    useEffect(() => {
        if (chats.length > 0) {
            scrollToBottom();
        }
    }, [chats]);

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
    }, [user, sessionId])

    return (
        <div className='font-mono p-5 flex flex-col items-center justify-center'>
            <ScrollArea ref={scrollAreaRef} className="h-[calc(100svh-30rem)] w-full lg:w-2/3 flex justify-center items-center lg:px-5">
                <div className="w-full">
                    {chats.sort((a, b) => (
                        new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
                    )).map((chat) => (
                        <ChatBubble
                            sender={chat.role}
                            key={chat.id}
                            isLoading={chat.state === "loading"}
                            isDone={chat.state === "done"}
                            timestamp={chat.created_at}
                            message={chat.content}
                        />
                    ))}
                </div>
            </ScrollArea>
            <form className="w-full lg:w-2/3 absolute bottom-20"
                onSubmit={async (e) => {
                    e.preventDefault()
                    if (!user) return
                    const { error } = await supabase.from("chat").insert({
                        role: "user",
                        content: prompt,
                        session_uid: sessionId,
                        user_uid: user.id,
                        state: "done"
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
                }}
            >
                <PromptInput
                    value={prompt}
                    onValueChange={(e) => setPrompt(e)}
                    isLoading={isLoading}
                >
                    <PromptInputTextarea
                        placeholder="Tanyakan pertanyaan Anda..."
                        onKeyDown={(e) => {
                            // Submit form when Enter is pressed without Shift key
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault(); // Prevent adding a new line
                                // Find and submit the form
                                e.currentTarget.closest('form')?.requestSubmit();
                            }
                        }}
                    />
                    <PromptInputActions className="justify-end pt-2">
                        <PromptInputAction
                            tooltip={isLoading ? "Stop generation" : "Send message"}
                        >
                            <Button
                                variant="default"
                                size="icon"
                                type="submit"
                                className="h-8 w-8 rounded-full bg-[#192f59]"
                            >
                                {isLoading ? (
                                    <Square className="size-5 fill-current" />
                                ) : (
                                    <ArrowUp className="size-5" />
                                )}
                            </Button>
                        </PromptInputAction>
                    </PromptInputActions>
                </PromptInput>
            </form>
        </div>
    )
}