export type User = { id: number; email: string; fullName: string }

export type Profile = {
  email: string
  fullName: string
  phone: string
  location: string
  linkedinUrl: string
  portfolioUrl: string
  collegeName: string
  degreeName: string
  enrollmentYear: number | null
  graduationYear: number | null
  professionalSummary: string
  skills: string
}

export type ResumeVersion = {
  id: number
  versionNumber: number
  filename: string
  parserMode: string
  notes: string
  createdAt: string
  textPreview: string
}

export type Resume = {
  id: number
  name: string
  category: string
  latestVersion: number
  createdAt: string
  versions: ResumeVersion[]
}

export type Metrics = {
  overall: number
  dimensions: { name: string; score: number }[]
  matchedKeywords: string[]
  missingKeywords: string[]
  suggestions: string[]
  readyForCoverLetter: boolean
}

export type Application = {
  id: number
  companyName: string
  roleTitle: string
  jobUrl: string
  metrics: Metrics
  coverLetter: string
  createdAt: string
}

