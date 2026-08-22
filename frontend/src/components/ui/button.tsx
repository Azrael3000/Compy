import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { Slot } from 'radix-ui'

import { cn } from '@/lib/utils'

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-normal transition-all disabled:pointer-events-none disabled:opacity-50 active:translate-y-px cursor-pointer',
  {
    variants: {
      variant: {
        default: 'bg-medium text-white hover:bg-dark',
        outline:
          'bg-transparent text-medium border border-light hover:bg-highlight hover:text-dark',
        destructive:
          'bg-transparent text-card-red border border-card-red hover:bg-card-red hover:text-white',
      },
      size: {
        default: 'px-3.5 py-1.5',
        sm: 'px-3 py-1',
        icon: 'size-9',
      },
    },
    defaultVariants: { variant: 'default', size: 'default' },
  },
)

function Button({
  className,
  variant = 'default',
  size = 'default',
  asChild = false,
  ...props
}: React.ComponentProps<'button'> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean
  }) {
  const Comp = asChild ? Slot.Root : 'button'

  return (
    <Comp
      data-slot="button"
      data-variant={variant}
      data-size={size}
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
}

export { Button, buttonVariants }
