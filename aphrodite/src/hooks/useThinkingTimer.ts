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
        chats.forEach((chat) => {
            if (chat.state === "loading" || chat.state === "searching" || chat.state === "extracting") {
                setThinkingStartTimes(prev => {
                    if (!prev[chat.id]) {
                        const startTime = chat.thinking_start_time
                            ? new Date(chat.thinking_start_time)
                            : new Date();

                        return {
                            ...prev,
                            [chat.id]: startTime
                        };
                    }
                    return prev;
                });
            } else if (chat.state === "streaming") {
                if (chat.thinking_duration && chat.thinking_duration > 0) {
                    setFinalThinkingDurations(prevDurations => {
                        if (!prevDurations[chat.id]) {
                            return {
                                ...prevDurations,
                                [chat.id]: chat.thinking_duration
                            };
                        }
                        return prevDurations;
                    });

                    setThinkingStartTimes(prev => {
                        const updated = { ...prev };
                        delete updated[chat.id];
                        return updated;
                    });
                }
            } else if (chat.state === "done" || chat.state === "error") {
                setThinkingStartTimes(prev => {
                    if (prev[chat.id]) {
                        const endTime = new Date();
                        const duration = endTime.getTime() - prev[chat.id].getTime();

                        setFinalThinkingDurations(prevDurations => ({
                            ...prevDurations,
                            [chat.id]: duration
                        }));

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