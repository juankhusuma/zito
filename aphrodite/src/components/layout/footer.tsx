import { Facebook, Linkedin, Twitter, Instagram, Mail, MapPin, Phone } from "lucide-react";
import { useEffect, useState } from "react";

export default function Footer() {
    const [isChat, setIsChat] = useState(false)
    useEffect(() => {
        if (window.location.href.includes("/chat")) setIsChat(true);
    }, [])
    if (isChat) return null;
    return (
        <footer className="z-[100] relative overflow-hidden lg:mt-0">
            <div className="bg-gradient-to-r from-[#151b2c] to-[#1a2339] py-16 lg:py-20 px-6 md:px-10 lg:px-16">
                <div className="container mx-auto">
                    <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-x-12 gap-y-10">
                        {/* Logo and Description Column */}
                        <div className="col-span-1 md:col-span-3 lg:col-span-1">
                            <div className="mb-6">
                                <img
                                    src="/logo-lexin-white.png"
                                    alt="lexin"
                                    className="max-w-[180px] lg:max-w-[220px] h-auto"
                                />
                            </div>
                            <p className="text-gray-400 text-sm leading-relaxed mb-6 max-w-md">
                                Lexin adalah platform AI yang dirancang untuk membuat informasi hukum Indonesia lebih mudah diakses dan dipahami oleh semua orang.
                            </p>
                            <div className="flex space-x-4 mb-6">
                                <a href="#" className="w-9 h-9 rounded-full bg-[#192f59] hover:bg-[#0d1e3f] flex items-center justify-center text-white transition-colors">
                                    <Facebook size={18} />
                                </a>
                                <a href="#" className="w-9 h-9 rounded-full bg-[#192f59] hover:bg-[#0d1e3f] flex items-center justify-center text-white transition-colors">
                                    <Twitter size={18} />
                                </a>
                                <a href="#" className="w-9 h-9 rounded-full bg-[#192f59] hover:bg-[#0d1e3f] flex items-center justify-center text-white transition-colors">
                                    <Linkedin size={18} />
                                </a>
                                <a href="#" className="w-9 h-9 rounded-full bg-[#192f59] hover:bg-[#0d1e3f] flex items-center justify-center text-white transition-colors">
                                    <Instagram size={18} />
                                </a>
                            </div>
                        </div>

                        {/* Links Columns */}
                        <div>
                            <h3 className="text-white font-bold text-lg mb-4">Explore</h3>
                            <div className="h-[3px] w-full bg-gradient-to-r from-[#d61b23] to-[#ff476e] rounded-full mb-5" />
                            <ul className="space-y-3">
                                <li>
                                    <a href="#" className="text-gray-400 hover:text-white transition-colors flex items-center">
                                        <span className="mr-2 text-xs">►</span>Research
                                    </a>
                                </li>
                                <li>
                                    <a href="#" className="text-gray-400 hover:text-white transition-colors flex items-center">
                                        <span className="mr-2 text-xs">►</span>Products
                                    </a>
                                </li>
                                <li>
                                    <a href="#" className="text-gray-400 hover:text-white transition-colors flex items-center">
                                        <span className="mr-2 text-xs">►</span>Publication
                                    </a>
                                </li>
                                <li>
                                    <a href="#" className="text-gray-400 hover:text-white transition-colors flex items-center">
                                        <span className="mr-2 text-xs">►</span>About Us
                                    </a>
                                </li>
                            </ul>
                        </div>

                        <div>
                            <h3 className="text-white font-bold text-lg mb-4">Connect</h3>
                            <div className="h-[3px] w-full bg-gradient-to-r from-[#d61b23] to-[#ff476e] rounded-full mb-5" />
                            <ul className="space-y-3">
                                <li>
                                    <a href="#" className="text-gray-400 hover:text-white transition-colors flex items-center">
                                        <span className="mr-2 text-xs">►</span>Our Team
                                    </a>
                                </li>
                                <li>
                                    <a href="#" className="text-gray-400 hover:text-white transition-colors flex items-center">
                                        <span className="mr-2 text-xs">►</span>Partners
                                    </a>
                                </li>
                                <li>
                                    <a href="#" className="text-gray-400 hover:text-white transition-colors flex items-center">
                                        <span className="mr-2 text-xs">►</span>Careers
                                    </a>
                                </li>
                                <li>
                                    <a href="#" className="text-gray-400 hover:text-white transition-colors flex items-center">
                                        <span className="mr-2 text-xs">►</span>Contact Us
                                    </a>
                                </li>
                            </ul>
                        </div>

                        <div>
                            <h3 className="text-white font-bold text-lg mb-4">Contact</h3>
                            <div className="h-[3px] w-full bg-gradient-to-r from-[#d61b23] to-[#ff476e] rounded-full mb-5" />
                            <ul className="space-y-4">
                                <li className="flex items-start">
                                    <MapPin className="mr-3 text-[#d61b23] flex-shrink-0 mt-1" size={18} />
                                    <span className="text-gray-400">Fakultas Ilmu Komputer, Universitas Indonesia, Depok, Jawa Barat 16424</span>
                                </li>
                                <li className="flex items-center">
                                    <Phone className="mr-3 text-[#d61b23] flex-shrink-0" size={18} />
                                    <span className="text-gray-400">(021) 786-3419</span>
                                </li>
                                <li className="flex items-center">
                                    <Mail className="mr-3 text-[#d61b23] flex-shrink-0" size={18} />
                                    <a href="mailto:contact@lexin.ai" className="text-gray-400 hover:text-white transition-colors">contact@lexin.ai</a>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>

            {/* Bottom Bar */}
            <div className="bg-[#111827] py-5 px-6 md:px-10 lg:px-16">
                <div className="container mx-auto flex flex-col md:flex-row justify-between items-center">
                    <p className="text-gray-500 text-sm mb-3 md:mb-0">
                        &copy; {new Date().getFullYear()} Lexin AI. All Rights Reserved.
                    </p>
                    <div className="flex space-x-6">
                        <a href="#" className="text-gray-500 hover:text-white text-sm transition-colors">Privacy Policy</a>
                        <a href="#" className="text-gray-500 hover:text-white text-sm transition-colors">Terms of Service</a>
                        <a href="#" className="text-gray-500 hover:text-white text-sm transition-colors">FAQ</a>
                    </div>
                </div>
            </div>
        </footer>
    )
}