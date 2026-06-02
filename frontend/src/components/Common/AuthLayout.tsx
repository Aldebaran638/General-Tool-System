import { Appearance } from "@/components/Common/Appearance"
import { Logo } from "@/components/Common/Logo"
import { Footer } from "./Footer"
import { BookOpen, Award, Users, BarChart3 } from "lucide-react"

interface AuthLayoutProps {
  children: React.ReactNode
}

export function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="grid min-h-svh lg:grid-cols-2">
      {/* Left brand panel */}
      <div className="relative hidden lg:flex lg:flex-col lg:items-center lg:justify-center overflow-hidden bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-800 dark:from-blue-900 dark:via-blue-950 dark:to-indigo-950">
        {/* Decorative background elements */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-40 -left-40 h-80 w-80 rounded-full bg-white/10 blur-3xl" />
          <div className="absolute -bottom-40 -right-40 h-80 w-80 rounded-full bg-indigo-400/20 blur-3xl" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-60 w-60 rounded-full bg-blue-400/10 blur-2xl" />
        </div>

        {/* Content */}
        <div className="relative z-10 flex flex-col items-center gap-8 px-12">
          <div className="flex flex-col items-center gap-4">
            <div className="rounded-2xl bg-white/10 p-4 backdrop-blur-sm">
              <Logo variant="full" className="h-12 brightness-0 invert" asLink={false} />
            </div>
            <div className="text-center">
              <h1 className="text-3xl font-bold text-white">课程培训及考核管理平台</h1>
              <p className="mt-2 text-blue-100">高效管理培训流程，智能考核评估</p>
            </div>
          </div>

          {/* Feature highlights */}
          <div className="grid grid-cols-2 gap-4 w-full max-w-sm">
            {[
              { icon: BookOpen, label: "在线课程", desc: "随时随地学习" },
              { icon: Award, label: "智能考核", desc: "自动化考试" },
              { icon: Users, label: "团队管理", desc: "高效协作" },
              { icon: BarChart3, label: "数据分析", desc: "精准洞察" },
            ].map((feature, i) => (
              <div
                key={i}
                className="flex flex-col items-center gap-2 rounded-xl bg-white/10 p-4 backdrop-blur-sm transition-all hover:bg-white/20"
              >
                <feature.icon className="h-6 w-6 text-white" />
                <span className="text-sm font-medium text-white">{feature.label}</span>
                <span className="text-xs text-blue-100">{feature.desc}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right form panel */}
      <div className="flex flex-col gap-4 p-6 md:p-10">
        <div className="flex justify-between items-center">
          {/* Mobile logo */}
          <div className="lg:hidden">
            <Logo variant="full" className="h-8" />
          </div>
          <div className="ml-auto">
            <Appearance />
          </div>
        </div>
        <div className="flex flex-1 items-center justify-center">
          <div className="w-full max-w-sm">{children}</div>
        </div>
        <Footer />
      </div>
    </div>
  )
}
