import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import supabase from "@/common/supabase";
import { Chat } from "@/pages/chat/Session";

/**
 * Custom hook for managing Supabase realtime subscriptions for chat messages
 * Handles INSERT, UPDATE, and DELETE events for chat messages in a session
 * @param sessionId - The session ID to subscribe to chat changes
 * @param userId - The user ID for subscription filtering
 * @param refetch - Function to refetch chat data when subscription is established
 */
export function useRealtimeSubscription(
    sessionId: string | undefined,
    userId: string | undefined,
    refetch: () => void
) {
    const queryClient = useQueryClient();

    useEffect(() => {
        if (!sessionId || !userId) return;

        const channel = supabase.channel(`chat::${userId}::${sessionId}`)
            .on("postgres_changes", {
                event: "INSERT",
                schema: "public",
                table: "chat",
                filter: `session_uid=eq.${sessionId}`
            }, (payload) => {
                console.log("New chat:", payload);
                console.log("Chat state:", payload.new.state);
                console.log("Chat role:", payload.new.role);
                queryClient.setQueryData(['chats', sessionId], (oldData: Chat[] = []) =>
                    [...oldData, payload.new as Chat]
                );
            })
            .on("postgres_changes", {
                event: "UPDATE",
                schema: "public",
                table: "chat",
                filter: `session_uid=eq.${sessionId}`
            }, (payload) => {
                console.log("Updated chat:", payload);
                queryClient.setQueryData(['chats', sessionId], (oldData: Chat[] = []) =>
                    oldData.map((chat) => chat.id === payload.new.id ? {
                        ...chat,
                        ...payload.new
                    } as Chat : chat)
                );
            })
            .on("postgres_changes", {
                event: "DELETE",
                schema: "public",
                table: "chat",
                filter: `session_uid=eq.${sessionId}`
            }, (payload) => {
                console.log("Deleted chat:", payload);
                queryClient.setQueryData(['chats', sessionId], (oldData: Chat[] = []) =>
                    oldData.filter((chat) => chat.id !== payload.old.id)
                );
            })
            .subscribe(async (status) => {
                console.log("Subscription status:", status);
                // Defensive refetch on successful subscription to cover missed events
                if (status === 'SUBSCRIBED') {
                    await refetch();
                }
            });

        return () => {
            console.log("Unsubscribing from chat channel");
            channel.unsubscribe();
        };
    }, [userId, sessionId, queryClient, refetch]);
}