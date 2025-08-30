import supabase from "@/common/supabase"
import {
    Sidebar,
    SidebarContent,
    SidebarFooter,
    SidebarGroup,
    SidebarGroupContent,
    SidebarGroupLabel,
    SidebarHeader,
    SidebarMenu,
    SidebarMenuAction,
    SidebarMenuButton,
    SidebarMenuItem,
    SidebarMenuSkeleton,
    SidebarSeparator,
    SidebarTrigger,
} from "@/components/ui/sidebar"
import { useAuth } from "@/hoc/AuthProvider"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { MessageSquarePlus, MoreHorizontal, Search, Trash2 } from "lucide-react"
import { useEffect, useState, useMemo } from "react"
import { useNavigate, useParams } from "react-router"
import PrimaryButton from "../button"
import { cn } from "@/lib/utils"
import { TooltipProvider, TooltipTrigger } from "@radix-ui/react-tooltip"
import { Tooltip, TooltipContent } from "../ui/tooltip"
import { Input } from "@/components/ui/input"
import { useQuery, useQueryClient } from '@tanstack/react-query'

interface Session {
    id: string
    title: string
    last_updated_at: string
    user_uid: string
}

const fetchSessions = async (userId: string): Promise<Session[]> => {
    const { data, error } = await supabase
        .from("session")
        .select("*")
        .eq("user_uid", userId)
        .order('last_updated_at', { ascending: false });
    
    if (error) {
        throw new Error(error.message);
    }
    
    return data || [];
};

export function AppSidebar() {
    const { user, loading } = useAuth()
    const navigate = useNavigate()
    const { sessionId } = useParams()
    const [searchQuery, setSearchQuery] = useState("")
    const queryClient = useQueryClient()

    const { 
        data: sessions = [], 
        isLoading: sidebarLoading 
    } = useQuery({
        queryKey: ['sessions', user?.id],
        queryFn: () => user?.id ? fetchSessions(user.id) : Promise.resolve([]),
        enabled: !!user?.id,
        staleTime: 3 * 60 * 1000, // 3 minutes
        refetchOnWindowFocus: true,
    })

    useEffect(() => {
        if (!loading && !user) {
            console.log("User not found, redirecting to login")
            window.location.href = "/login?next=/chat"
        }
    }, [user, loading])

    useEffect(() => {
        if (!user?.id) return;

        const channel = supabase.realtime.channel(`session:${user.id}`)
            .on("postgres_changes", {
                schema: "public",
                table: "session",
                event: "UPDATE",
                filter: `user_uid=eq.${user.id}`
            }, (payload) => {
                console.log("Updated session:", payload)
                queryClient.setQueryData(['sessions', user.id], (oldData: Session[] = []) => 
                    oldData.map((session) =>
                        session.id === payload.new.id ? payload.new as Session : session)
                );
            })
            .on("postgres_changes", {
                schema: "public",
                table: "session",
                event: "INSERT",
                filter: `user_uid=eq.${user.id}`
            }, (payload) => {
                console.log("New session:", payload)
                queryClient.setQueryData(['sessions', user.id], (oldData: Session[] = []) => 
                    [payload.new as Session, ...oldData]
                );
            })
            .on("postgres_changes", {
                schema: "public",
                table: "session",
                event: "DELETE",
                filter: `user_uid=eq.${user.id}`
            }, (payload) => {
                console.log("Deleted session:", payload)
                queryClient.setQueryData(['sessions', user.id], (oldData: Session[] = []) => 
                    oldData.filter(session => session.id !== payload.old.id)
                );
            })

        channel.subscribe((status, err) => {
            console.log("Realtime session status:", status)
            if (err) {
                console.error("Realtime session error:", err)
            }
        })

        return () => {
            console.log("Unsubscribing from realtime channel")
            supabase.realtime.removeChannel(channel)
        }
    }, [user?.id, queryClient])

    const groups = useMemo(() => {
        const today = new Date()
        const todayString = today.toISOString().split("T")[0]
        
        const todayChatSessions = sessions.filter((session) => {
            const sessionDate = new Date(session.last_updated_at)
            return sessionDate.toISOString().split("T")[0] === todayString
        })
        
        const yesterdayChatSessions = sessions.filter((session) => {
            const sessionDate = new Date(session.last_updated_at)
            const yesterday = new Date(today)
            yesterday.setDate(today.getDate() - 1)
            return sessionDate.toISOString().split("T")[0] === yesterday.toISOString().split("T")[0]
        })

        const lastWeekChatSessions = sessions.filter((session) => {
            const sessionDate = new Date(session.last_updated_at)
            const lastWeek = new Date(today)
            const yesterday = new Date(today)
            yesterday.setDate(today.getDate() - 1)
            lastWeek.setDate(today.getDate() - 7)
            return sessionDate >= lastWeek && sessionDate < yesterday && !yesterdayChatSessions.includes(session)
        })
        
        const lastMonthChatSessions = sessions.filter((session) => {
            const sessionDate = new Date(session.last_updated_at)
            const lastMonth = new Date(today)
            lastMonth.setMonth(today.getMonth() - 1)
            return (sessionDate >= lastMonth && sessionDate < today
                && !lastWeekChatSessions.includes(session)
                && !yesterdayChatSessions.includes(session)
                && !todayChatSessions.includes(session)
            )
        })

        const groupedOlderChatSessions: { [key: string]: Session[] } = {}
        const olderChatSessions = sessions.filter((session) => {
            const sessionDate = new Date(session.last_updated_at)
            const lastMonth = new Date(today)
            lastMonth.setMonth(today.getMonth() - 1)
            lastMonth.setDate(today.getDate() - 1)
            return sessionDate < lastMonth && !lastMonthChatSessions.includes(session)
                && !lastWeekChatSessions.includes(session)
                && !yesterdayChatSessions.includes(session)
                && !todayChatSessions.includes(session)
        })
        
        olderChatSessions.forEach((session) => {
            const sessionDate = new Date(session.last_updated_at)
            const monthYear = sessionDate.toLocaleString("default", { month: "long", year: "numeric" })
            if (!groupedOlderChatSessions[monthYear]) {
                groupedOlderChatSessions[monthYear] = []
            }
            groupedOlderChatSessions[monthYear].push(session)
        })

        const sortByDate = (a: Session, b: Session) => new Date(b.last_updated_at).getTime() - new Date(a.last_updated_at).getTime();
        
        todayChatSessions.sort(sortByDate)
        yesterdayChatSessions.sort(sortByDate)
        lastWeekChatSessions.sort(sortByDate)
        lastMonthChatSessions.sort(sortByDate)
        
        Object.keys(groupedOlderChatSessions).forEach((key) => {
            groupedOlderChatSessions[key].sort(sortByDate)
        })

        return {
            "Today": todayChatSessions,
            "Yesterday": yesterdayChatSessions,
            "Previous 7 Days": lastWeekChatSessions,
            "Previous 30 Days": lastMonthChatSessions,
            ...groupedOlderChatSessions,
        }
    }, [sessions])

    const filteredGroups = useMemo(() => {
        if (!searchQuery.trim()) {
            return groups;
        }

        const query = searchQuery.toLowerCase();
        const filtered: { [key: string]: Session[] } = {};

        Object.entries(groups).forEach(([groupName, groupSessions]) => {
            const matchingSessions = groupSessions.filter(
                session => session.title.toLowerCase().includes(query)
            );

            if (matchingSessions.length > 0) {
                filtered[groupName] = matchingSessions;
            }
        });

        return filtered;
    }, [searchQuery, groups]);

    return (
        <Sidebar collapsible="offcanvas" className="absolute border-t h-full flex-1 bg-gray-100 shadow-sm z-[50]">
            <TooltipProvider>
                <SidebarHeader className="p-3">
                    <div className="flex flex-col gap-3">
                        <div className="flex items-center justify-between">
                            <SidebarTrigger className="cursor-pointer lg:hidden p-1.5 hover:bg-gray-100 rounded-full transition-colors" />
                        </div>

                        <PrimaryButton
                            className="flex items-center gap-2 justify-center bg-[#192f59] hover:bg-[#0d1e3f] transition-colors py-2.5 rounded-lg text-white shadow-sm"
                            onClick={() => navigate("/chat")}
                        >
                            <MessageSquarePlus size={16} />
                            <span className="text-sm font-medium">New Chat</span>
                        </PrimaryButton>

                        <div className="relative">
                            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-400" />
                            <Input
                                placeholder="Search conversations..."
                                className="pl-9 py-2 h-9 text-sm border-gray-200 focus-visible:ring-[#192f59] focus-visible:ring-offset-0"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                            />
                        </div>
                    </div>
                    <SidebarSeparator className="mt-3" />
                </SidebarHeader>

                <SidebarContent className="px-2">
                    {(sidebarLoading && sessions.length === 0) && (
                        <SidebarMenu>
                            {Array.from({ length: 6 }).map((_, index) => (
                                <SidebarMenuItem key={index} className="mb-1">
                                    <SidebarMenuSkeleton className="h-10" />
                                </SidebarMenuItem>
                            ))}
                        </SidebarMenu>
                    )}

                    {!sidebarLoading && Object.keys(filteredGroups).length === 0 && searchQuery && (
                        <div className="p-4 text-center text-gray-500">
                            <p className="text-sm">No conversations found</p>
                        </div>
                    )}

                    {!sidebarLoading && Object.entries(filteredGroups)
                        .filter(([_, sessions]) => sessions.length > 0)
                        .map(([group, sessions]) => (
                            <SidebarGroup key={group}>
                                <SidebarGroupLabel className="px-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    {group}
                                </SidebarGroupLabel>
                                <SidebarGroupContent>
                                    <SidebarMenu>
                                        {sessions.map((session) => (
                                            <SidebarMenuItem
                                                key={session.id}
                                                className={cn(
                                                    "cursor-pointer group/session rounded-md mb-1 overflow-hidden",
                                                    sessionId === session.id ? "bg-[#192f59]/10" : "hover:bg-gray-100"
                                                )}
                                            >
                                                <Tooltip>
                                                    <TooltipTrigger asChild>
                                                        <span className="flex-1">
                                                            <SidebarMenuButton asChild>
                                                                <div
                                                                    onClick={() => navigate(session.id)}
                                                                    className={cn(
                                                                        "flex items-center py-2 pl-3 pr-1 text-sm font-medium truncate transition-colors",
                                                                        sessionId === session.id ? "text-[#192f59]" : "text-gray-700"
                                                                    )}
                                                                >
                                                                    <span className="truncate">{session.title}</span>
                                                                </div>
                                                            </SidebarMenuButton>
                                                        </span>
                                                    </TooltipTrigger>
                                                    <TooltipContent side="right">{session.title}</TooltipContent>
                                                </Tooltip>

                                                <DropdownMenu>
                                                    <DropdownMenuTrigger asChild>
                                                        <SidebarMenuAction>
                                                            <div className="p-1.5 hover:bg-gray-200 rounded-full transition-colors">
                                                                <MoreHorizontal className="h-4 w-4 text-gray-500" />
                                                            </div>
                                                        </SidebarMenuAction>
                                                    </DropdownMenuTrigger>
                                                    <DropdownMenuContent side="right" align="start" className="w-48">
                                                        <DropdownMenuItem
                                                            onClick={async () => {
                                                                if (!user) return;
                                                                const { error } = await supabase.from("session").delete().eq("id", session.id)
                                                                if (error) {
                                                                    console.error("Error deleting session:", error)
                                                                    return;
                                                                }
                                                                if (sessionId === session.id) {
                                                                    navigate("/chat")
                                                                }
                                                                // Update React Query cache
                                                                queryClient.setQueryData(['sessions', user.id], (oldData: Session[] = []) => 
                                                                    oldData.filter(s => s.id !== session.id)
                                                                );
                                                            }}
                                                            className="text-red-600 cursor-pointer focus:bg-red-50 focus:text-red-700"
                                                        >
                                                            <Trash2 className="h-4 w-4 mr-2" />
                                                            <span>Delete Conversation</span>
                                                        </DropdownMenuItem>
                                                    </DropdownMenuContent>
                                                </DropdownMenu>
                                            </SidebarMenuItem>
                                        ))}
                                    </SidebarMenu>
                                </SidebarGroupContent>
                            </SidebarGroup>
                        ))}
                </SidebarContent>
                <SidebarFooter className="p-3 border-t">
                    <div className="text-xs text-center text-gray-500">
                        <p>Lexin Chat © {new Date().getFullYear()}</p>
                    </div>
                </SidebarFooter>
            </TooltipProvider>
        </Sidebar>
    )
}