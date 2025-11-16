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
import { Skeleton } from "@/components/ui/skeleton";
import { useQuery } from '@tanstack/react-query';
import { useThinkingTimer } from "@/hooks/useThinkingTimer";
import { useRealtimeSubscription } from "@/hooks/useRealtimeSubscription";
import { useChat } from "@/hooks/useChat";

export interface Chat {
    id: string;
    role: "user" | "assistant";
    content: string;
    created_at: string;
    user_uid: string;
    session_uid: string;
    context?: string;
    is_liked?: boolean;
    is_disliked?: boolean;
    documents?: string;
    citations?: {
        number: number;
        doc_id: string;
        title: string;
        url: string;
    }[];
    state: "done" | "loading" | "error" | "generating" | "searching" | "extracting";
    thinking_start_time?: string;
    thinking_duration?: number;
}

const fetchChats = async (sessionId: string): Promise<Chat[]> => {
    const { data, error } = await supabase
        .from("chat")
        .select("*")
        .eq("session_uid", sessionId)
        .order('created_at', { ascending: true });
    
    if (error) {
        throw new Error(error.message);
    }
    
    return data || [];
};

export default function Session() {
    const navigate = useNavigate()
    const { sessionId } = useParams()
    const { user, loading } = useAuth()
    const [prompt, setPrompt] = React.useState("")
    const scrollAreaRef = useRef<HTMLDivElement>(null)

    // Query for chat messages
    const {
        data: chats = [],
        isLoading: isPageLoading,
        refetch
    } = useQuery({
        queryKey: ['chats', sessionId],
        queryFn: () => sessionId ? fetchChats(sessionId) : Promise.resolve([]),
        enabled: !!sessionId && !!user,
        staleTime: Infinity, // Realtime handles freshness
        refetchOnWindowFocus: false,
        refetchOnReconnect: false,
    })

    const [isLoading, setIsLoading] = React.useState(false)
    const { thinkingStartTimes, finalThinkingDurations } = useThinkingTimer(chats)
    const { newSessionChat, continueChat } = useChat(user)

    // Setup realtime subscription
    useRealtimeSubscription(sessionId, user?.id, refetch)


    const scrollToBottom = () => {
        if (scrollAreaRef.current) {
            const scrollContainer = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]');
            if (scrollContainer) {
                scrollContainer.scrollTop = scrollContainer.scrollHeight;
            }
        }
    }

    useEffect(() => {
        const hasLoading = chats.some((chat) => chat.state === "loading")
        console.log("DEBUG: chats state check:", {
            totalChats: chats.length,
            hasLoading,
            loadingStates: chats.map(c => ({ id: c.id, state: c.state, role: c.role }))
        })
        setIsLoading(hasLoading)
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

    const welcomeChats = useMemo(() => {
        if (sessionId) return [];
        return [{
            id: "start",
            content: "Halo! Selamat datang di **Lexin Chat!** Saya adalah **asisten virtual** Anda. Silakan ajukan **pertanyaan** atau beri tahu saya **apa yang dapat saya bantu**. Saya akan melakukan yang terbaik untuk **membantu** Anda. Mari kita mulai! 😊🙏",
            role: "assistant" as const,
            created_at: new Date(0).toISOString(),
            user_uid: user?.id || "",
            session_uid: "",
            state: "done" as const,
            context: undefined
        }];
    }, [sessionId, user?.id]);


    const memoizedChatList = useMemo(() => {
        const chatData = sessionId ? chats : welcomeChats;
        return chatData
            .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
            .map((chat) => (
                <ChatBubble
                    chat={chat}
                    sender={chat.role}
                    key={chat.id}
                    isLoading={chat.state === "loading"}
                    isDone={chat.state === "done"}
                    isSearching={chat.state === "searching"}
                    isExtracting={chat.state === "extracting"}
                    isError={chat.state === "error"}
                    timestamp={chat.created_at}
                    message={chat.content}
                    context={chat?.context}
                    history={chatData}
                    sessionId={sessionId || ""}
                    messageId={chat.id}
                    thinkingStartTime={thinkingStartTimes[chat.id]}
                    finalThinkingDuration={('thinking_duration' in chat ? chat.thinking_duration : null) || finalThinkingDurations[chat.id]}
                />
            ));
    }, [chats, welcomeChats, sessionId, thinkingStartTimes, finalThinkingDurations]);

    return (
        <div className='h-full w-full bg-gradient-to-b from-gray-50 to-gray-100 flex flex-col'>
            <ScrollArea ref={scrollAreaRef} className="w-full flex-1 px-2 sm:px-4 md:px-8 lg:px-12 h-[500px]">
                {
                    (isPageLoading && sessionId && chats.length === 0) ? (
                        Array.from({ length: 25 }).map((_, index) => (
                            <div className="w-full flex max-w-4xl mx-auto" style={{
                                justifyContent: Math.random() > 0.2 ? "flex-start" : "flex-end",
                            }} key={index}>
                                <Skeleton key={index} className="w-full h-2 my-1 rounded-md" style={{
                                    width: `${Math.max(Math.random() * 50, 10)}%`,
                                    height: `${Math.max(Math.random() * 35, 25)}px`,
                                }} />
                            </div>
                        ))
                    )
                        :
                        (<div className="w-full max-w-4xl mx-auto py-3 sm:py-6 mb-20 sm:mb-24 md:mb-32">
                            {memoizedChatList}
                        </div>)
                }
            </ScrollArea>
            <div className="sticky bottom-0 left-0 right-0 bg-gradient-to-t from-white via-white to-transparent pt-3 sm:pt-6 pb-2 sm:pb-4 px-2 sm:px-4 md:px-8 lg:px-12 z-10 mt-auto">
                <form className="w-full max-w-4xl mx-auto"
                    onSubmit={async (e) => {
                        e.preventDefault()
                        if (!user) return

                        if (!sessionId) {
                            await newSessionChat(prompt);
                        } else {
                            await continueChat(prompt, sessionId, chats);
                        }

                        setPrompt("")
                    }}
                >
                    {!sessionId && (
                        <div className="mb-3 sm:mb-4">
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-2 max-h-24 sm:max-h-32 overflow-y-auto">
                                {randomQuestions.map((question => (
                                    <Button
                                        key={question}
                                        variant="outline"
                                        className="w-full py-2 sm:py-3 px-3 sm:px-4 cursor-pointer border border-[#192f59]/30 text-[#192f59] hover:bg-[#192f59]/10 hover:border-[#192f59] transition-all text-left justify-start rounded-lg"
                                        onClick={async () => {
                                            await newSessionChat(question)
                                            scrollToBottom()
                                        }}
                                    >
                                        <p className="text-wrap text-xs sm:text-sm">{question}</p>
                                    </Button>
                                )))}
                            </div>
                        </div>
                    )}
                    <div className="bg-white rounded-xl sm:rounded-2xl shadow-lg border border-gray-200 overflow-hidden transition-all hover:shadow-xl">
                        <PromptInput
                            value={prompt}
                            onValueChange={(e) => setPrompt(e)}
                            isLoading={isLoading}
                            className="border-none focus-within:ring-0"
                        >
                            <div className="flex flex-col">
                                <PromptInputTextarea
                                    placeholder="Tanyakan pertanyaan Anda..."
                                    className="min-h-[60px] sm:min-h-[70px] py-3 sm:py-4 px-3 sm:px-5 focus:ring-0 focus-visible:ring-0 border-none resize-none text-sm sm:text-base"
                                    onKeyDown={(e) => {
                                        // Submit form when Enter is pressed without Shift key
                                        if (e.key === 'Enter' && !e.shiftKey) {
                                            e.preventDefault(); // Prevent adding a new line
                                            // Find and submit the form
                                            e.currentTarget.closest('form')?.requestSubmit();
                                        }
                                    }}
                                />
                                <div className="flex items-center justify-between px-3 sm:px-4 py-2 sm:py-3 bg-gray-50 border-t border-gray-100">
                                    <div className="text-xs text-gray-500 hidden sm:block">
                                        Press <kbd className="px-1.5 py-0.5 bg-gray-100 border border-gray-300 rounded text-xs font-mono">Enter</kbd> to send, <kbd className="px-1.5 py-0.5 bg-gray-100 border border-gray-300 rounded text-xs font-mono">Shift+Enter</kbd> for new line
                                    </div>
                                    <div className="text-xs text-gray-500 sm:hidden">
                                        <kbd className="px-1.5 py-0.5 bg-gray-100 border border-gray-300 rounded text-xs font-mono">Enter</kbd> to send
                                    </div>
                                    <PromptInputActions className="justify-end">
                                        <PromptInputAction
                                            tooltip={isLoading ? "Stop generation" : "Send message"}
                                        >
                                            <Button
                                                variant="default"
                                                size="icon"
                                                type="submit"
                                                disabled={prompt.trim().length === 0}
                                                className={`h-8 w-8 sm:h-10 sm:w-10 rounded-full shadow-md transition-all ${prompt.trim().length === 0 ? 'bg-gray-300' : 'bg-[#192f59] hover:bg-[#0d1e3f]'}`}
                                            >
                                                {isLoading ? (
                                                    <Square className="size-3 sm:size-4 fill-current" />
                                                ) : (
                                                    <ArrowUp className="size-3 sm:size-4" />
                                                )}
                                            </Button>
                                        </PromptInputAction>
                                    </PromptInputActions>
                                </div>
                            </div>
                        </PromptInput>
                    </div>
                </form>
            </div>
        </div>
    )
}