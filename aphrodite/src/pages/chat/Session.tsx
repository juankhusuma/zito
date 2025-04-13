import React, { useEffect, useRef, useMemo } from "react";
import { useNavigate, useParams } from "react-router";
import { useAuth } from "../../hoc/AuthProvider";
import supabase from "../../common/supabase";
import { PromptInput, PromptInputAction, PromptInputActions, PromptInputTextarea } from "@/components/ui/prompt-input";
import { Button } from "@/components/ui/button";
import { ArrowUp, Square } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import ChatBubble from "@/components/chat/bubble";
import { randomQuestions } from "@/utils/getRecommendation";

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

    const newSessionChat = async (question: string) => {
        if (!user || !question || question.trim() === "") return
        const { data: sessions, error: sessionCreateError } = await supabase.from("session").insert({
            user_uid: user.id,
            title: "Untitled Chat",
        }).select()
        if (sessionCreateError) {
            console.error("Error creating session:", sessionCreateError)
            return
        }
        const sessionId = sessions[0].id
        const { data: chats, error: chatInsertError } = await supabase.from("chat").insert({
            role: "user",
            content: question,
            session_uid: sessionId,
            user_uid: user.id,
            state: "done"
        }).select()
        if (chatInsertError) {
            console.error("Error inserting chat:", chatInsertError)
            return
        }
        const { data: authSessions } = await supabase.auth.getSession()
        if (!authSessions.session) {
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
                access_token: authSessions.session?.access_token,
                refresh_token: authSessions.session?.refresh_token,
                messages: chats.map((chat) => ({
                    content: chat.content,
                    role: chat.role,
                    timestamp: chat.created_at
                }))
            })
        })
        const json = await res.json()
        console.log("Response:", json)
        setPrompt("")
        navigate(`/chat/${sessionId}`)
    }

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
            navigate("/login?next=/chat")
        }
    }, [user, loading, navigate])

    useEffect(() => {
        if (chats.length > 0) {
            scrollToBottom();
        }
    }, [chats]);

    useEffect(() => {
        if (!user) return
        if (!sessionId) return setChats([{
            id: "start",
            content: "Halo! Selamat datang di **Lexin Chat!** Saya adalah **asisten virtual** Anda. Silakan ajukan **pertanyaan** atau beri tahu saya **apa yang dapat saya bantu**. Saya akan melakukan yang terbaik untuk **membantu** Anda. Mari kita mulai! 😊🙏",
            role: "assistant",
            created_at: new Date(0).toISOString(),
            user_uid: user?.id || "",
            session_uid: sessionId || "",
            state: "generating"
        }]);
        supabase.from("chat").select("*").eq("session_uid", sessionId).then(({ data, error }) => {
            if (error) {
                console.error("Error fetching chats:", error)
                return
            }
            setChats(data)
            console.log("Fetched chats:", data)
        })

        supabase.channel(`chat::${user.id}::${sessionId}`)
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

    const memoizedChatList = useMemo(() => {
        return chats
            .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
            .map((chat) => (
                <ChatBubble
                    sender={chat.role}
                    key={chat.id}
                    isLoading={chat.state === "loading"}
                    isDone={chat.state === "done"}
                    timestamp={chat.created_at}
                    message={chat.content}
                />
            ));
    }, [chats]);

    return (
        <div className='font-mono p-5 flex flex-col items-center justify-center'>
            <ScrollArea ref={scrollAreaRef} className="h-[calc(100svh-30rem)] w-full flex justify-center items-center lg:px-5">
                <div className="w-full">
                    {memoizedChatList}
                </div>
            </ScrollArea>
            <form className="w-full px-10 absolute bottom-20"
                onSubmit={async (e) => {
                    e.preventDefault()
                    if (!user) return
                    if (!sessionId) return await newSessionChat(prompt);
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
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-2 mb-4">
                    {!sessionId && randomQuestions.map((question => (
                        <Button
                            key={question}
                            variant="outline"
                            className="w-full py-5 cursor-pointer border-[#192f59] text-[#192f59] hover:bg-[#192f59] hover:text-white"
                            onClick={async () => {
                                await newSessionChat(question)
                                scrollToBottom()
                            }}
                        >
                            <p className="lowercase text-wrap text-sm">{question}</p>
                        </Button>
                    )))}
                </div>
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