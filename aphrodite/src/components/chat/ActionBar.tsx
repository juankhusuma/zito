import { useState } from "react";
import { ThumbsUp, ThumbsDown, RotateCcw, Clipboard } from "lucide-react";
import { useAuth } from "@/hoc/AuthProvider";
import supabase from "@/common/supabase";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { Chat } from "@/pages/chat/Session";

interface ActionBarProps {
    text: string;
    history: any[];
    sessionId: string;
    messageId: string;
    chat: Chat;
    finalThinkingDuration?: number;
}

export function ActionBar(props: ActionBarProps) {
    const { user } = useAuth();
    const [isLiked, setIsLiked] = useState(!!props.chat.is_liked);
    const [isDisliked, setIsDisliked] = useState(!!props.chat.is_disliked);

    const formatFinalDuration = (ms: number): string => {
        if (ms < 1000) {
            return `${ms} ms`;
        } else if (ms < 10000) {
            return `${(ms / 1000).toFixed(1)} s`;
        } else if (ms < 60000) {
            return `${Math.round(ms / 1000)} s`;
        } else {
            const minutes = Math.floor(ms / 60000);
            const seconds = Math.round((ms % 60000) / 1000);
            return `${minutes}m ${seconds}s`;
        }
    };

    return (
        <div className="flex items-center gap-3">
            <ThumbsUp onClick={() => {
                setIsLiked(true);
                setIsDisliked(false);
                supabase.from("chat").update({
                    is_liked: true,
                    is_disliked: false
                }).eq("id", props.messageId).then(() => {
                    toast("Upvoted the result")
                })
            }} size={15} color="#192f59" className={cn("cursor-pointer transition-all",
                isLiked ? "fill-[#192f59] hover:fill-none" : "hover:fill-[#192f59] hover:opacity-80"
            )} />
            <ThumbsDown onClick={() => {
                setIsDisliked(true);
                setIsLiked(false);
                supabase.from("chat").update({
                    is_liked: false,
                    is_disliked: true
                }).eq("id", props.messageId).then(() => {
                    toast("Downvoted the result")
                })
            }} size={15} color="#192f59" className={cn("cursor-pointer transition-all",
                isDisliked ? "fill-[#192f59] hover:fill-none" : "hover:opacity-80"
            )} />
            <RotateCcw onClick={async () => {
                try {
                    const lastMessage = props.history[props.history.length - 1];
                    const { error: deleteError } = await supabase.from("chat").delete().eq("id", lastMessage.id);
                    if (deleteError) {
                        console.error("Failed to delete last message:", deleteError);
                        toast("Failed to delete previous message");
                        return;
                    }

                    const { data, error: sessionError } = await supabase.auth.getSession();
                    if (sessionError) {
                        console.error("Failed to get session:", sessionError);
                        toast("Authentication error");
                        return;
                    }
                    if (!data.session) {
                        console.error("No session found");
                        toast("Please log in again");
                        return;
                    }

                    const response = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/chat`, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            session_uid: props.sessionId,
                            user_uid: user?.id,
                            access_token: data.session.access_token,
                            refresh_token: data.session.refresh_token,
                            messages: [...props.history?.map((chat) => ({
                                content: chat.content,
                                role: chat.role,
                                timestamp: chat.created_at
                            }))]
                        })
                    });

                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }

                    toast("Regenerating response");
                } catch (error) {
                    console.error("Failed to regenerate response:", error);
                    toast("Failed to regenerate response");
                }
            }} size={15} color="#192f59" className="cursor-pointer transition-all" />
            <Clipboard onClick={async () => {
                try {
                    await navigator.clipboard.writeText(props.text);
                    toast("Copied to clipboard");
                } catch (error) {
                    console.error("Failed to copy to clipboard:", error);
                    toast("Failed to copy to clipboard");
                }
            }} size={15} color="#192f59" className="hover:fill-[#192f59] cursor-pointer transition-all" />

            {/* Display final thinking duration */}
            {props.finalThinkingDuration && props.finalThinkingDuration > 500 && (
                <div className="text-xs text-gray-500 ml-2 flex items-center gap-1">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="12" cy="12" r="10"/>
                        <polyline points="12,6 12,12 16,14"/>
                    </svg>
                    <span>Berpikir {formatFinalDuration(props.finalThinkingDuration)}</span>
                </div>
            )}
        </div>
    )
}