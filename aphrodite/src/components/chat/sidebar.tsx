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
import { MoreHorizontal, Trash2 } from "lucide-react"
import React, { useEffect } from "react"
import { useNavigate, useParams } from "react-router"
import PrimaryButton from "../button"
import { cn } from "@/lib/utils"
import { TooltipProvider, TooltipTrigger } from "@radix-ui/react-tooltip"
import { Tooltip, TooltipContent } from "../ui/tooltip"

interface Session {
    id: string
    title: string
    last_updated_at: string
    user_uid: string
}

export function AppSidebar() {
    const { user, loading } = useAuth()
    const [sessions, setSessions] = React.useState<Session[]>([])
    const navigate = useNavigate()
    const [groups, setGroups] = React.useState<{ [key: string]: Session[] }>({})
    const [sidebarLoading, setSidebarLoading] = React.useState(false)
    const { sessionId } = useParams()

    useEffect(() => {
        setSidebarLoading(true)
        if (!loading && !user) {
            console.log("User not found, redirecting to login")
            window.location.href = "/login?next=/chat"
            return;
        }

        // Fetch initial sessions
        supabase.from("session").select("*")
            .eq("user_uid", user?.id)
            .then(({ data, error }) => {
                if (error) {
                    console.error("Error fetching sessions:", error)
                    return
                }
                setSessions(data || [])
                setSidebarLoading(false)
            })

        // Setup realtime subscription
        const channel = supabase.realtime.channel(`session:${user?.id}`)
            .on("postgres_changes", {
                schema: "public",
                table: "session",
                event: "UPDATE",
                filter: `user_uid=eq.${user?.id}`
            }, (payload) => {
                console.log("Updated session:", payload)
                setSessions((prev) => prev.map((session) =>
                    session.id === payload.new.id ? payload.new as Session : session)
                )
            })
            .on("postgres_changes", {
                schema: "public",
                table: "session",
                event: "INSERT",
                filter: `user_uid=eq.${user?.id}`
            }, (payload) => {
                console.log("New session:", payload)
                setSessions((prev) => [payload.new as Session, ...prev])
            })

        channel.subscribe((status, err) => {
            console.log("Realtime session status:", status)
            if (err) {
                console.error("Realtime session error:", err)
            }
        })

        // Cleanup subscription when component unmounts
        return () => {
            console.log("Unsubscribing from realtime channel")
            supabase.realtime.removeChannel(channel)
        }
    }, [user, loading])

    useEffect(() => {
        // today
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

        // sort all sessions by last_updated_at
        todayChatSessions.sort((a, b) => new Date(b.last_updated_at).getTime() - new Date(a.last_updated_at).getTime())
        yesterdayChatSessions.sort((a, b) => new Date(b.last_updated_at).getTime() - new Date(a.last_updated_at).getTime())
        lastWeekChatSessions.sort((a, b) => new Date(b.last_updated_at).getTime() - new Date(a.last_updated_at).getTime())
        lastMonthChatSessions.sort((a, b) => new Date(b.last_updated_at).getTime() - new Date(a.last_updated_at).getTime())
        Object.keys(groupedOlderChatSessions).forEach((key) => {
            groupedOlderChatSessions[key].sort((a, b) => new Date(b.last_updated_at).getTime() - new Date(a.last_updated_at).getTime())
        })


        setGroups({
            "Today": todayChatSessions,
            "Yesterday": yesterdayChatSessions,
            "Previous 7 Days": lastWeekChatSessions,
            "Previous 30 Days": lastMonthChatSessions,
            ...groupedOlderChatSessions,
        })

        console.log(groups)
        console.log(sessions)
    }, [sessions])


    return (
        <Sidebar collapsible="offcanvas" className="absolute border-t h-[calc(100svh-16rem)]">
            <TooltipProvider>
                <SidebarHeader >
                    <div className="flex items-center justify-between gap-4 px-4 py-2">
                        <PrimaryButton className="flex-1" onClick={() => {
                            navigate("/chat")
                        }}>
                            <p className="text-sm text-center w-full font-bold">Add New Chat</p>
                        </PrimaryButton>
                        <SidebarTrigger className="cursor-pointer lg:hidden" />
                    </div>
                    <SidebarSeparator />
                </SidebarHeader>
                <SidebarContent>
                    {
                        sidebarLoading && (
                            <SidebarMenu>
                                {Array.from({ length: 20 }).map((_, index) => (
                                    <SidebarMenuItem key={index} className="pl-5">
                                        <SidebarMenuSkeleton className="" />
                                    </SidebarMenuItem>
                                ))}
                            </SidebarMenu>
                        )
                    }
                    {
                        !sidebarLoading && Object.entries(groups).filter((group) => {
                            const sessions = groups[group[0]]
                            return sessions.length > 0
                        }).map(([group, sessions]) => (
                            <SidebarGroup key={group}>
                                <SidebarGroupLabel>{group}</SidebarGroupLabel>
                                <SidebarGroupContent>
                                    <SidebarMenu>
                                        {sessions.map((session) => (
                                            <SidebarMenuItem key={session.id} className="cursor-pointer group/session">
                                                <Tooltip>
                                                    <TooltipTrigger asChild>
                                                        <span className="flex-1">
                                                            <SidebarMenuButton asChild className="group-hover/session:visible">
                                                                <div onClick={() => navigate(session.id)} className={cn("flex items-center text-slate-800 text-sm font-semibold",
                                                                    sessionId === session.id && "bg-[#192f59] text-white"
                                                                )}>
                                                                    <span>{session.title}</span>
                                                                </div>
                                                            </SidebarMenuButton>
                                                        </span>
                                                    </TooltipTrigger>
                                                    <TooltipContent>{session.title}</TooltipContent>
                                                </Tooltip>

                                                <DropdownMenu>
                                                    <DropdownMenuTrigger asChild>
                                                        <SidebarMenuAction>
                                                            <MoreHorizontal className={cn(
                                                                sessionId === session.id && "text-white group-hover/session:text-[#192f59] cursor-pointer"
                                                            )} />
                                                        </SidebarMenuAction>
                                                    </DropdownMenuTrigger>
                                                    <DropdownMenuContent side="right" align="start">
                                                        <DropdownMenuItem onClick={async () => {
                                                            if (!user) return;
                                                            const { error } = await supabase.from("session").delete().eq("id", session.id)
                                                            if (error) {
                                                                console.error("Error deleting session:", error)
                                                            }
                                                            if (sessionId === session.id) {
                                                                navigate("/chat")
                                                            }
                                                            setSessions((prev) => prev.filter((s) => s.id !== session.id))
                                                            setGroups((prev) => {
                                                                const newGroups = { ...prev }
                                                                const groupSessions = newGroups[group]
                                                                newGroups[group] = groupSessions.filter((s) => s.id !== session.id)
                                                                return newGroups
                                                            })
                                                        }} className="text-xs text-[#192f59] font-medium cursor-pointer">
                                                            <Trash2 />
                                                            <span>Delete Project</span>
                                                        </DropdownMenuItem>
                                                    </DropdownMenuContent>
                                                </DropdownMenu>
                                            </SidebarMenuItem>
                                        ))}
                                    </SidebarMenu>
                                </SidebarGroupContent>
                            </SidebarGroup>
                        ))
                    }
                </SidebarContent>
                <SidebarFooter />
            </TooltipProvider>
        </Sidebar>
    )
}
