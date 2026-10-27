import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../ui/dialog'
import { WorkspaceSidebar } from './WorkspaceSidebar'

export function WorkspaceMobileDirectory({
  open,
  onOpenChange,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="top-0 left-0 flex h-dvh w-[280px] max-w-[86vw] translate-x-0 translate-y-0 flex-col gap-0 overflow-hidden rounded-none border-r p-0 sm:max-w-[280px]">
        <DialogHeader className="sr-only">
          <DialogTitle>工作台目录</DialogTitle>
          <DialogDescription>工作台主要导航</DialogDescription>
        </DialogHeader>
        <WorkspaceSidebar
          onNavigate={() => onOpenChange(false)}
          className="min-h-0 flex-1 border-r-0"
        />
      </DialogContent>
    </Dialog>
  )
}
