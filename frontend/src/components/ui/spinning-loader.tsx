import React from "react";
import { Loader2 } from "lucide-react"; // Ensure you have this dependency installed

interface SpinningLoaderProps {
    size?: number; // Optional size prop for the loader
    color?: string; // Optional color prop for the loader
}

const SpinningLoader: React.FC<SpinningLoaderProps> = ({ size = 12, color = "gray-500" }) => {
    return (
        <div className="flex items-center justify-center h-screen">
            <Loader2
                className={`w-${size} h-${size} text-${color}`}
                style={{ animation: "spin 1s linear infinite" }}
            />
        </div>
    );
};

export default SpinningLoader;