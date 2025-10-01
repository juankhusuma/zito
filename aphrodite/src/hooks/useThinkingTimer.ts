import { useState, useEffect } from "react";
import { Chat } from "@/pages/chat/Session";

/**
 * Custom hook for managing thinking time tracking across chat messages
 * Tracks start times for loading/searching/extracting states and calculates final durations
 * @param chats - Array of chat messages to monitor for state changes
 * @returns Object with thinking start times and final durations for each chat
 */
export function useThinkingTimer(chats: Chat[]) {
    const [thinkingStartTimes, setThinkingStartTimes] = useState<Record<string, Date>>({});
    const [finalThinkingDurations, setFinalThinkingDurations] = useState<Record<string, number>>({});

    useEffect(() => {
        // Track thinking start times for loading chats
        chats.forEach((chat) => {
            if (chat.state === "loading" || chat.state === "searching" || chat.state === "extracting") {
                setThinkingStartTimes(prev => {
                    // Only set if not already tracking this chat
                    if (!prev[chat.id]) {
                        return {
                            ...prev,
                            [chat.id]: new Date()
                        };
                    }
                    return prev;
                });
            } else if (chat.state === "done" || chat.state === "error") {
                // Calculate final thinking duration before cleanup
                setThinkingStartTimes(prev => {
                    if (prev[chat.id]) {
                        const endTime = new Date();
                        const duration = endTime.getTime() - prev[chat.id].getTime();

                        // Store final duration
                        setFinalThinkingDurations(prevDurations => ({
                            ...prevDurations,
                            [chat.id]: duration
                        }));

                        // Clean up start time
                        const updated = { ...prev };
                        delete updated[chat.id];
                        return updated;
                    }
                    return prev;
                });
            }
        });
    }, [chats]);

    return {
        thinkingStartTimes,
        finalThinkingDurations
    };
}