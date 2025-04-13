import { Loader } from "@mantine/core";

interface ButtonProps {
    onClick?: () => void;
    type?: "button" | "submit" | "reset";
    className?: string;
    disabled?: boolean;
    fullWidth?: boolean;
    children?: React.ReactNode;
    isLoading?: boolean
}

export default function PrimaryButton({ onClick = () => { }, isLoading = false, type = "button", className, disabled, fullWidth, children }: ButtonProps) {
    return (
        <button
            className={`disabled:cursor-default cursor-pointer disabled:bg-[#d61b24cb] hover:bg-[#d61b24cb] flex flex-row items-center bg-[#d61b23] font-semibold text-white py-3 px-6 rounded-sm ${fullWidth ? 'w-full' : 'min-w-14'} ${className}`}
            type={type}
            onClick={onClick}
            disabled={disabled || isLoading}
        >
            {isLoading ? <Loader size="xs" color="#192f59" className="mr-3" /> : <></>}
            {children}
        </button>
    )
}