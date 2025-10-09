import { useCallback } from "react";
import { useNavigate } from "react-router";
import supabase from "@/common/supabase";
import { Chat } from "@/pages/chat/Session";

/**
 * Custom hook for chat operations including new session creation and message continuation
 * @param user - The authenticated user object
 * @returns Object with chat operation functions
 */
export function useChat(user: any) {
    const navigate = useNavigate();

    const newSessionChat = useCallback(async (question: string) => {
        if (!user || !question || question.trim() === "") return;

        const { data: sessions, error: sessionCreateError } = await supabase.from("session").insert({
            user_uid: user.id,
            title: "Untitled Chat",
        }).select();

        if (sessionCreateError) {
            console.error("Error creating session:", sessionCreateError);
            return;
        }

        const sessionId = sessions[0].id;
        const { data: chats, error: chatInsertError } = await supabase.from("chat").insert({
            role: "user",
            content: question,
            session_uid: sessionId,
            user_uid: user.id,
            state: "done"
        }).select();

        if (chatInsertError) {
            console.error("Error inserting chat:", chatInsertError);
            return;
        }

        const { data: authSessions } = await supabase.auth.getSession();
        if (!authSessions.session) {
            console.error("No session found");
            return;
        }

        // Navigate first to setup subscription, then send message
        navigate(`/chat/${sessionId}`);

        // Wait a bit for subscription to establish
        await new Promise(resolve => setTimeout(resolve, 100));

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
                    content: chat.context ? `
                    <context>
                    ${chat.context}
                    </context>\n\n
                    ` : "" + chat.content,
                    role: chat.role,
                    timestamp: chat.created_at
                }))
            })
        });

        const json = await res.json();
        console.log("Response:", json);
    }, [user, navigate]);

    const continueChat = useCallback(async (
        prompt: string,
        sessionId: string | undefined,
        chats: Chat[]
    ) => {
        if (!user || !prompt || prompt.trim() === "" || !sessionId) return;

        const { error: chatInsertError } = await supabase.from("chat").insert({
            role: "user",
            content: prompt,
            session_uid: sessionId,
            user_uid: user.id,
            state: "done"
        }).select();

        if (chatInsertError) {
            console.error("Error inserting chat:", chatInsertError);
            return;
        }

        const { data } = await supabase.auth.getSession();
        if (!data.session) {
            console.error("No session found");
            return;
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
        });

        const json = await res.json();
        console.log("Response:", json);
    }, [user]);

    return {
        newSessionChat,
        continueChat
    };
}