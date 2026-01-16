import { BarChart3 } from 'lucide-react'
import React from 'react'

const Navbar = () => {
  return (
     <div className="bg-teal-700 text-white py-6 shadow-md">
        <div className="max-w-5xl mx-auto px-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-white rounded-lg">
              {/* Simple Logo Placeholder */}
              <BarChart3 className="text-teal-700 w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold">ZamZam Bank ARS</h1>
              <p className="text-teal-100 text-sm">
                Automated Reconciliation System
              </p>
            </div>
          </div>
        </div>
      </div>
  )
}

export default Navbar