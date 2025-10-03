import { useEffect, useMemo } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import supabase from "@/common/supabase";

export interface Session {
    id: string;
    title: string;
    last_updated_at: string;
    user_uid: string;
}

const fetchSessions = async (userId: string): Promise<Session[]> => {
    const { data, error } = await supabase
        .from("session")
        .select("*")
        .eq("user_uid", userId)
        .order("last_updated_at", { ascending: false });

    if (error) {
        throw new Error(error.message);
    }
    return data || [];
};

// Helper functions for date grouping
const dateKey = (d: Date) =>
    `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;

const startOfDay = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate());

/**
 * Custom hook for managing chat sessions with realtime updates and grouping
 * @param userId - The user ID to fetch sessions for
 * @returns Object with sessions data, loading state, and grouped sessions
 */
export function useSessions(userId: string | undefined) {
    const queryClient = useQueryClient();

    const {
        data: sessions = [],
        isLoading: sidebarLoading,
    } = useQuery({
        queryKey: ["sessions", userId],
        queryFn: () => (userId ? fetchSessions(userId) : Promise.resolve([])),
        enabled: !!userId,
        staleTime: 3 * 60 * 1000, // 3 minutes
        refetchOnWindowFocus: true,
    });

    // Realtime update sessions
    useEffect(() => {
        if (!userId) return;

        const channel = supabase.realtime.channel(`session:${userId}`)
            .on("postgres_changes", {
                schema: "public",
                table: "session",
                event: "UPDATE",
                filter: `user_uid=eq.${userId}`,
            }, (payload) => {
                queryClient.setQueryData(["sessions", userId], (oldData: Session[] = []) =>
                    oldData.map((s) => (s.id === payload.new.id ? (payload.new as Session) : s))
                );
            })
            .on("postgres_changes", {
                schema: "public",
                table: "session",
                event: "INSERT",
                filter: `user_uid=eq.${userId}`,
            }, (payload) => {
                queryClient.setQueryData(["sessions", userId], (oldData: Session[] = []) =>
                    [payload.new as Session, ...oldData]
                );
            })
            .on("postgres_changes", {
                schema: "public",
                table: "session",
                event: "DELETE",
                filter: `user_uid=eq.${userId}`,
            }, (payload) => {
                queryClient.setQueryData(["sessions", userId], (oldData: Session[] = []) =>
                    oldData.filter((s) => s.id !== payload.old.id)
                );
            });

        channel.subscribe();

        return () => {
            supabase.realtime.removeChannel(channel);
        };
    }, [userId, queryClient]);

    // Group sessions by date
    const groups = useMemo(() => {
        const now = new Date();
        const todayStart = startOfDay(now);
        const yesterdayStart = new Date(todayStart); yesterdayStart.setDate(todayStart.getDate() - 1);
        const weekStart = new Date(todayStart); weekStart.setDate(todayStart.getDate() - 7);
        const monthStart = new Date(todayStart); monthStart.setMonth(todayStart.getMonth() - 1);

        const kToday = dateKey(now);
        const kYesterday = dateKey(yesterdayStart);

        const dOf = (iso: string) => new Date(iso);
        const kOf = (iso: string) => dateKey(dOf(iso));
        const sod = (iso: string) => startOfDay(dOf(iso));

        const todayChatSessions = sessions.filter((s) => kOf(s.last_updated_at) === kToday);
        const yesterdayChatSessions = sessions.filter((s) => kOf(s.last_updated_at) === kYesterday);

        const lastWeekChatSessions = sessions.filter((s) => {
            const d = sod(s.last_updated_at);
            return d >= weekStart && d < yesterdayStart;
        });

        const lastMonthChatSessions = sessions.filter((s) => {
            const d = sod(s.last_updated_at);
            return d >= monthStart && d < weekStart;
        });

        const groupedOlderChatSessions: Record<string, Session[]> = {};
        sessions.forEach((s) => {
            const d = sod(s.last_updated_at);
            if (d < monthStart) {
                const label = d.toLocaleString("id-ID", { month: "long", year: "numeric" });
                (groupedOlderChatSessions[label] ??= []).push(s);
            }
        });

        const sortByDate = (a: Session, b: Session) =>
            dOf(b.last_updated_at).getTime() - dOf(a.last_updated_at).getTime();

        [todayChatSessions, yesterdayChatSessions, lastWeekChatSessions, lastMonthChatSessions]
            .forEach((arr) => arr.sort(sortByDate));
        Object.values(groupedOlderChatSessions).forEach((arr) => arr.sort(sortByDate));

        return {
            "Today": todayChatSessions,
            "Yesterday": yesterdayChatSessions,
            "Previous 7 Days": lastWeekChatSessions,
            "Previous 30 Days": lastMonthChatSessions,
            ...groupedOlderChatSessions,
        };
    }, [sessions]);

    return {
        sessions,
        sidebarLoading,
        groups
    };
}