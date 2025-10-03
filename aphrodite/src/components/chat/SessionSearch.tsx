import { useMemo } from "react";
import { Input } from "@/components/ui/input";
import { Search } from "lucide-react";
import { Session } from "@/hooks/useSessions";

interface SessionSearchProps {
    searchQuery: string;
    onSearchChange: (value: string) => void;
    groups: Record<string, Session[]>;
}

/**
 * Search component for filtering chat sessions with grouped results
 * @param searchQuery - Current search query string
 * @param onSearchChange - Callback when search query changes
 * @param groups - Grouped sessions to filter
 * @returns Filtered groups based on search query
 */
export function useSessionSearch(searchQuery: string, groups: Record<string, Session[]>) {
    return useMemo(() => {
        if (!searchQuery.trim()) return groups;

        const query = searchQuery.toLowerCase();
        const filtered: { [key: string]: Session[] } = {};

        Object.entries(groups).forEach(([label, sessions]) => {
            const matches = sessions.filter((s) =>
                s.title.toLowerCase().includes(query)
            );
            if (matches.length > 0) filtered[label] = matches;
        });

        return filtered;
    }, [searchQuery, groups]);
}

/**
 * Session search input component
 */
export function SessionSearch({ searchQuery, onSearchChange }: Omit<SessionSearchProps, 'groups'>) {
    return (
        <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
                type="search"
                placeholder="Search chats..."
                value={searchQuery}
                onChange={(e) => onSearchChange(e.target.value)}
                className="pl-9 py-2 bg-white border-gray-200 focus:border-[#192f59] focus:ring-[#192f59] rounded-lg text-sm"
            />
        </div>
    );
}