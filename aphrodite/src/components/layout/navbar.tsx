import { Sheet, SheetTrigger, SheetContent } from "@/components/ui/sheet"
import { Button } from "@/components/ui/button"
import { Icon } from "@iconify/react/dist/iconify.js";
import { useAuth } from "@/hoc/AuthProvider";
import { Skeleton } from "../ui/skeleton";
import supabase from "@/common/supabase";
import { useState } from "react";

export default function Navbar() {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <div className="w-full">
            {/* Top bar */}
            <div className="flex justify-end px-4 sm:px-8 xl:px-32 bg-[#192f59]">
                <p className="bg-[#d61b23] text-white text-sm sm:text-lg h-full flex py-2 sm:py-3 xl:py-4 px-4 sm:px-8 font-bold">
                    Faculty of Computer Science
                </p>
            </div>

            {/* Main navbar */}
            <header className="sticky top-0 w-full bg-white shadow-sm border-b border-gray-200 z-50">
                <div className="flex items-center justify-between px-4 sm:px-8 xl:px-32 py-4">
                    {/* Logo */}
                    <div className="flex-shrink-0">
                        <a href="/" className="flex items-center">
                            <img
                                src="/logo-lexin.png"
                                alt="lexin"
                                className="h-12 sm:h-16 lg:h-20 w-auto"
                            />
                        </a>
                    </div>

                    {/* Desktop Navigation */}
                    <nav className="hidden md:flex items-center space-x-8">
                        <UserProfile />
                    </nav>

                    {/* Mobile menu button */}
                    <div className="md:hidden">
                        <Sheet open={isOpen} onOpenChange={setIsOpen}>
                            <SheetTrigger asChild>
                                <Button variant="ghost" size="sm">
                                    <MenuIcon className="h-6 w-6 text-[#192f59]" />
                                </Button>
                            </SheetTrigger>
                            <SheetContent side="right" className="w-[300px] sm:w-[400px]">
                                <div className="flex flex-col space-y-6 mt-8">
                                    <div className="pt-6 border-t border-gray-200">
                                        <UserProfile mobile />
                                    </div>
                                </div>
                            </SheetContent>
                        </Sheet>
                    </div>
                </div>
            </header>
        </div>
    )
}


function UserProfile({ mobile = false }: { mobile?: boolean }) {
    const { loading, user, setLoading } = useAuth()

    if (loading) {
        return (
            <div className={`flex items-center space-x-3 ${mobile ? 'justify-start' : ''}`}>
                <Skeleton className="h-10 w-10 rounded-full" />
                <div className="space-y-2">
                    <Skeleton className="h-4 w-[150px]" />
                    <Skeleton className="h-3 w-[120px]" />
                </div>
            </div>
        )
    }

    const containerClass = mobile
        ? "flex flex-col space-y-4 p-5"
        : "flex items-center space-x-3";

    return (
        <div className={containerClass}>
            {user ? (
                <div className={`flex ${mobile ? 'flex-col space-y-3' : 'items-center space-x-3'}`}>
                    <div className={`flex items-center ${mobile ? 'space-x-3' : 'space-x-2'}`}>
                        <Icon
                            icon="mdi:account-circle"
                            className="text-[#192f59] text-3xl sm:text-4xl"
                        />
                        <div className="text-[#192f59] font-semibold">
                            <p className={`${mobile ? 'text-lg' : 'text-sm sm:text-base'} truncate max-w-[180px]`}>
                                {user.email}
                            </p>
                        </div>
                    </div>
                    <Button
                        variant="outline"
                        size={mobile ? "default" : "sm"}
                        onClick={async () => {
                            setLoading(true)
                            await supabase.auth.signOut()
                            setLoading(false)
                        }}
                        className="text-[#192f59] border-[#192f59] hover:bg-[#192f59] hover:text-white transition-colors"
                    >
                        <Icon icon="mdi:logout" className="mr-2 h-4 w-4" />
                        Logout
                    </Button>
                </div>
            ) : (
                <a
                    href="/login"
                    className="flex items-center space-x-2 text-[#192f59] hover:text-[#d61b23] transition-colors"
                >
                    <Icon
                        icon="mdi:account-circle"
                        className="text-3xl sm:text-4xl"
                    />
                    <span className="font-semibold">Login</span>
                </a>
            )}
        </div>
    )
}

function MenuIcon(props: any) {
    return (
        <svg
            {...props}
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
        >
            <line x1="4" x2="20" y1="12" y2="12" />
            <line x1="4" x2="20" y1="6" y2="6" />
            <line x1="4" x2="20" y1="18" y2="18" />
        </svg>
    )
}