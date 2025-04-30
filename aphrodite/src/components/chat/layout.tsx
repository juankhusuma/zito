import { SidebarProvider, SidebarTrigger } from "../ui/sidebar";
import { AppSidebar } from "./sidebar";
import { Outlet } from "react-router";

export default function ChatLayout() {
    return (
        <div className="relative">
            <SidebarProvider>
                <AppSidebar />
                <main className="lg:relative absolute flex w-full border-t flex-col">
                    <SidebarTrigger className="mt-5 cursor-pointer ml-2" />
                    <div className="w-full relative">
                        <Outlet />
                    </div>
                </main>
            </SidebarProvider>
        </div>
    )
}