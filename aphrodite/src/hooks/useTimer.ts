import { useState, useEffect, useCallback } from "react";

/**
 * Custom hook for timer functionality with real-time updates
 * @param startTime - The start time for the timer
 * @param isActive - Whether the timer should be active
 * @returns Object with elapsedTime and formatTime function
 */
export function useTimer(startTime?: Date, isActive: boolean = false) {
    const [elapsedTime, setElapsedTime] = useState(0);

    useEffect(() => {
        if (!startTime || !isActive) {
            setElapsedTime(0);
            return;
        }

        const interval = setInterval(() => {
            const now = new Date();
            const elapsed = now.getTime() - startTime.getTime();
            setElapsedTime(elapsed);
        }, 100); // Update every 100ms for smooth display

        return () => clearInterval(interval);
    }, [startTime, isActive]);

    const formatTime = useCallback((ms: number): string => {
        if (ms < 1000) {
            return `${Math.round(ms)} ms`;
        } else if (ms < 10000) {
            return `${(ms / 1000).toFixed(1)} s`;
        } else if (ms < 60000) {
            return `${Math.round(ms / 1000)} s`;
        } else {
            const minutes = Math.floor(ms / 60000);
            const seconds = Math.round((ms % 60000) / 1000);
            return `${minutes}m ${seconds}s`;
        }
    }, []);

    return { elapsedTime, formatTime };
}