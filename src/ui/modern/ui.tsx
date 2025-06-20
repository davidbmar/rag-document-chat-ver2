"use client"

import { useState, useEffect, useCallback } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Progress } from "@/components/ui/progress"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Alert, AlertDescription } from "@/components/ui/alert"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import rehypeHighlight from "rehype-highlight"
import {
  Upload,
  Search,
  MessageSquare,
  Activity,
  FileText,
  Trash2,
  Download,
  CheckCircle,
  AlertCircle,
  Clock,
  Database,
  Server,
  Copy,
  Filter,
  Loader2,
} from "lucide-react"

// API Client and Types
import apiClient from "./lib/api/client"
import type {
  SearchResult,
  DocumentInfo,
  SystemStatus,
  SearchContext,
  UploadProgress,
  ApiError
} from "./lib/api/types"
import { formatErrorForUser } from "./lib/utils/errorHandler"

export default function RAGDocumentChatUI() {
  const [activeTab, setActiveTab] = useState("browse")
  const [searchQuery, setSearchQuery] = useState("")
  const [question, setQuestion] = useState("")
  const [uploadProgress, setUploadProgress] = useState<UploadProgress>({ progress: 0, isUploading: false })
  
  // API State
  const [documents, setDocuments] = useState<Record<string, DocumentInfo>>({})
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null)
  const [lastSearchId, setLastSearchId] = useState<string | null>(null)
  const [searchContext, setSearchContext] = useState<SearchContext | null>(null)
  const [useSearchContext, setUseSearchContext] = useState(false)
  const [searchStrategy, setSearchStrategy] = useState<'basic' | 'enhanced' | 'paragraph'>('enhanced')
  const [topK, setTopK] = useState<number>(5)
  
  // Loading States
  const [isLoading, setIsLoading] = useState(false)
  const [isSearching, setIsSearching] = useState(false)
  const [isAsking, setIsAsking] = useState(false)
  const [answer, setAnswer] = useState<string | null>(null)
  const [answerSources, setAnswerSources] = useState<string[]>([])
  const [rawCitations, setRawCitations] = useState<any[]>([])
  const [conversationHistory, setConversationHistory] = useState<Array<{question: string, answer: string, sources: string[], rawCitations?: any[], timestamp: Date, usedContext: boolean, searchStrategy: string}>>([])  
  
  // System Prompt (Answer Style)
  const [systemPrompt, setSystemPrompt] = useState<string>("Create a short brief summary at the top. Then reply your answer in Markdown.")
  
  // Error State
  const [error, setError] = useState<string | null>(null)

  // Helper function to clear error after a delay
  const clearError = useCallback(() => {
    setTimeout(() => setError(null), 5000)
  }, [])
  
  // Load initial data
  useEffect(() => {
    // Add a small delay to ensure the component is mounted
    const initializeData = async () => {
      try {
        await loadDocuments()
        await loadSystemStatus()
      } catch (err) {
        console.error('Failed to initialize data:', err)
        setError('Failed to connect to API server. Please ensure it is running.')
      }
    }
    
    initializeData()
    
    // Set up periodic status updates
    const statusInterval = setInterval(() => {
      loadSystemStatus().catch(err => {
        console.warn('Status update failed:', err)
      })
    }, 10000) // Update every 10 seconds
    
    return () => clearInterval(statusInterval)
  }, [])
  
  // Clear error when it's set
  useEffect(() => {
    if (error) {
      clearError()
    }
  }, [error, clearError])

  // API Functions
  const loadDocuments = async () => {
    try {
      setIsLoading(true)
      const response = await apiClient.getDocuments()
      setDocuments(response.documents || {})
    } catch (err) {
      setError(formatErrorForUser(err))
    } finally {
      setIsLoading(false)
    }
  }
  
  const loadSystemStatus = async () => {
    try {
      const status = await apiClient.getStatus()
      setSystemStatus(status)
    } catch (err) {
      console.error('System status error:', err)
      setError(formatErrorForUser(err))
      // Reset system status on error to avoid showing stale data
      setSystemStatus(null)
    }
  }
  
  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return
    
    const file = files[0]
    setUploadProgress({ progress: 0, isUploading: true, filename: file.name })
    
    try {
      const response = await apiClient.uploadDocument(file, false)
      
      if (response.status === 'already_exists') {
        setError(`Document already exists: ${file.name}`)
      } else {
        // Reload documents after successful upload
        await loadDocuments()
      }
    } catch (err) {
      setError(formatErrorForUser(err))
    } finally {
      setUploadProgress({ progress: 100, isUploading: false })
      // Reset progress after a delay
      setTimeout(() => {
        setUploadProgress({ progress: 0, isUploading: false })
      }, 2000)
    }
  }
  
  const handleSearch = async () => {
    if (!searchQuery.trim()) return
    
    setIsSearching(true)
    try {
      const response = await apiClient.search({ 
        query: searchQuery,
        top_k: topK,
        return_chunks: true
      })
      
      setSearchResults(response.results)
      setLastSearchId(response.search_id)
      setSearchContext({
        query: searchQuery,
        results: response.total_results,
        documents: response.unique_documents,
        search_id: response.search_id
      })
    } catch (err) {
      setError(formatErrorForUser(err))
    } finally {
      setIsSearching(false)
    }
  }
  
  const handleAskQuestion = async () => {
    if (!question.trim()) return
    
    setIsAsking(true)
    try {
      const request: any = {
        question: question,
        top_k: topK,
        search_strategy: searchStrategy,
        system_prompt: systemPrompt.trim()
      }
      
      if (useSearchContext && searchContext?.search_id) {
        request.search_id = searchContext.search_id
      }
      
      // Add conversation history to the request
      if (conversationHistory.length > 0) {
        const recentHistory = conversationHistory
          .slice(-3) // Last 3 Q&A pairs
          .map(h => `Q: ${h.question}\nA: ${h.answer}`)
          .join('\n\n')
        request.conversation_history = recentHistory
      }
      
      const response = await apiClient.ask(request)
      setAnswer(response.answer)
      setAnswerSources(response.sources)
      setRawCitations(response.raw_citations || [])
      
      // Add to conversation history
      setConversationHistory(prev => [...prev, {
        question,
        answer: response.answer,
        sources: response.sources || [],
        rawCitations: response.raw_citations || [],
        timestamp: new Date(),
        usedContext: useSearchContext,
        searchStrategy: searchStrategy
      }])
      
      // Clear the question input
      setQuestion('')
    } catch (err) {
      setError(formatErrorForUser(err))
    } finally {
      setIsAsking(false)
    }
  }
  
  const handleClearDocuments = async () => {
    if (!confirm('Are you sure you want to clear all documents?')) return
    
    setIsLoading(true)
    try {
      await apiClient.clearDocuments()
      setDocuments({})
      setSearchResults([])
      setSearchContext(null)
      setAnswer(null)
      setAnswerSources([])
      setConversationHistory([])
      await loadSystemStatus()
    } catch (err) {
      setError(formatErrorForUser(err))
    } finally {
      setIsLoading(false)
    }
  }

  // Convert documents object to array for display
  const documentsArray = Object.entries(documents).map(([filename, info]) => ({
    name: filename,
    chunks: info.total_chunks,
    status: info.status,
    size: 'N/A' // Backend doesn't provide size currently
  }))

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 p-4">
      {/* Error Display */}
      {error && (
        <Alert className="mb-4 border-red-200 bg-red-50">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-slate-900">RAG Document Chat System</h1>
              <p className="text-slate-600 mt-1">Intelligent document processing and Q&A platform</p>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant={systemStatus?.api === "healthy" ? "default" : "destructive"} className="gap-1">
                <div
                  className={`w-2 h-2 rounded-full ${systemStatus?.api === "healthy" ? "bg-green-500" : "bg-red-500"}`}
                />
                {systemStatus?.api === "healthy" ? "System Online" : "System Error"}
              </Badge>
              {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
            </div>
          </div>
        </div>

        {/* Main Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-4 mb-6">
            <TabsTrigger value="browse" className="flex items-center gap-2">
              <Upload className="w-4 h-4" />
              Browse
            </TabsTrigger>
            <TabsTrigger value="search" className="flex items-center gap-2">
              <Search className="w-4 h-4" />
              Search
            </TabsTrigger>
            <TabsTrigger value="ask" className="flex items-center gap-2">
              <MessageSquare className="w-4 h-4" />
              Ask
            </TabsTrigger>
            <TabsTrigger value="status" className="flex items-center gap-2">
              <Activity className="w-4 h-4" />
              Status
            </TabsTrigger>
          </TabsList>

          {/* Browse Tab */}
          <TabsContent value="browse" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Upload Section */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Upload className="w-5 h-5" />
                    Upload Documents
                  </CardTitle>
                  <CardDescription>Upload PDF, TXT, or image files for processing</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div 
                    className="border-2 border-dashed border-slate-300 rounded-lg p-8 text-center hover:border-slate-400 transition-colors cursor-pointer"
                    onClick={() => document.getElementById('file-upload')?.click()}
                    onDrop={(e) => {
                      e.preventDefault()
                      handleFileUpload(e.dataTransfer.files)
                    }}
                    onDragOver={(e) => e.preventDefault()}
                  >
                    <input
                      id="file-upload"
                      type="file"
                      accept=".pdf,.txt,.png,.jpg,.jpeg"
                      onChange={(e) => handleFileUpload(e.target.files)}
                      className="hidden"
                    />
                    <Upload className="w-12 h-12 text-slate-400 mx-auto mb-4" />
                    <p className="text-slate-600 mb-2">Drag & drop files here or click to browse</p>
                    <p className="text-sm text-slate-500">Supports PDF, TXT, PNG, JPG, JPEG (max 50MB)</p>
                  </div>

                  {uploadProgress.isUploading && (
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Uploading {uploadProgress.filename}...</span>
                        <span>{uploadProgress.progress}%</span>
                      </div>
                      <Progress value={uploadProgress.progress} className="w-full" />
                    </div>
                  )}

                  <div className="flex gap-2">
                    <Button onClick={() => document.getElementById('file-upload')?.click()} disabled={uploadProgress.isUploading} className="flex-1">
                      {uploadProgress.isUploading ? 'Uploading...' : 'Upload Files'}
                    </Button>
                    <Button variant="outline" disabled={uploadProgress.isUploading}>
                      Advanced Processing
                    </Button>
                  </div>
                </CardContent>
              </Card>

              {/* Document List */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        <FileText className="w-5 h-5" />
                        Documents ({Object.keys(documents).length})
                      </CardTitle>
                      <CardDescription>Manage your uploaded documents</CardDescription>
                    </div>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="text-red-600 hover:text-red-700"
                      onClick={handleClearDocuments}
                    >
                      <Trash2 className="w-4 h-4 mr-1" />
                      Clear All
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-64">
                    <div className="space-y-3">
                      {documentsArray.map((doc, index) => (
                        <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <FileText className="w-4 h-4 text-slate-500" />
                              <span className="font-medium text-sm">{doc.name}</span>
                              <Badge variant={doc.status === "processed" ? "default" : "secondary"} className="text-xs">
                                {doc.status === "processed" ? (
                                  <CheckCircle className="w-3 h-3 mr-1" />
                                ) : (
                                  <Clock className="w-3 h-3 mr-1" />
                                )}
                                {doc.status}
                              </Badge>
                            </div>
                            <div className="text-xs text-slate-500">
                              {doc.chunks} chunks • {doc.size}
                            </div>
                          </div>
                          <div className="flex items-center gap-1">
                            <Button variant="ghost" size="sm">
                              <Download className="w-4 h-4" />
                            </Button>
                            <Button variant="ghost" size="sm" className="text-red-600">
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Search Tab */}
          <TabsContent value="search" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Search className="w-5 h-5" />
                  Document Search
                </CardTitle>
                <CardDescription>Search across all processed documents with advanced filtering</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-2">
                  <Input
                    placeholder="Enter your search query..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                    className="flex-1"
                  />
                  <Button onClick={handleSearch} disabled={isSearching || !searchQuery.trim()}>
                    {isSearching ? (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Search className="w-4 h-4 mr-2" />
                    )}
                    {isSearching ? 'Searching...' : 'Search'}
                  </Button>
                  <Button variant="outline">
                    <Filter className="w-4 h-4 mr-2" />
                    Filters
                  </Button>
                </div>

                {searchQuery && (
                  <Alert>
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      Found {searchResults.length} results for "{searchQuery}" in {systemStatus?.documents || 0} documents
                    </AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>

            {/* Search Results */}
            {searchQuery && (
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>Search Results</CardTitle>
                      <CardDescription>Results ranked by relevance score</CardDescription>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          if (searchContext) {
                            setActiveTab("ask")
                            setUseSearchContext(true)
                          }
                        }}
                      >
                        <MessageSquare className="w-4 h-4 mr-2" />
                        Ask Questions About These Results
                      </Button>
                      <Button variant="outline" size="sm">
                        <Download className="w-4 h-4 mr-2" />
                        Export Results
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-center gap-2 text-blue-800 text-sm">
                      <Database className="w-4 h-4" />
                      <span>
                        Search ID: {lastSearchId} • {searchResults.length} results from{" "}
                        {Array.from(new Set(searchResults.map((r) => r.document))).length} documents
                      </span>
                    </div>
                  </div>

                  <ScrollArea className="h-96">
                    <div className="space-y-4">
                      {searchResults.map((result, index) => (
                        <div key={index} className="border rounded-lg p-4 hover:bg-slate-50 transition-colors">
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <Badge variant="outline" className="text-xs">
                                Score: {result.score}
                              </Badge>
                              <Badge variant="secondary" className="text-xs">
                                {result.collection}
                              </Badge>
                            </div>
                            <div className="flex gap-1">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => {
                                  setQuestion(`Tell me more about: "${result.content.substring(0, 50)}..."`)
                                  setActiveTab("ask")
                                  setUseSearchContext(true)
                                }}
                              >
                                <MessageSquare className="w-4 h-4" />
                              </Button>
                              <Button variant="ghost" size="sm">
                                <Copy className="w-4 h-4" />
                              </Button>
                            </div>
                          </div>
                          <p className="text-sm text-slate-700 mb-2">{result.content}</p>
                          <div className="flex items-center gap-2 text-xs text-slate-500">
                            <FileText className="w-3 h-3" />
                            <span>{result.document}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Ask Tab */}
          <TabsContent value="ask" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-300px)]">
              {/* Left Column: Question Input & Answer (2/3 width) */}
              <div className="lg:col-span-2 flex flex-col space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <MessageSquare className="w-5 h-5" />
                      Ask a Question
                    </CardTitle>
                    <CardDescription>Get intelligent answers based on your documents</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Search Context Indicator */}
                    {searchContext && (
                      <Alert className={useSearchContext ? "border-blue-200 bg-blue-50" : "border-slate-200"}>
                        <Database className="h-4 w-4" />
                        <AlertDescription className="flex items-center justify-between">
                          <div>
                            <span className="font-medium">Search Context Available:</span> "{searchContext.query}" (
                            {searchContext.results} results from {searchContext.documents.length} documents)
                          </div>
                          <div className="flex items-center gap-2">
                            <label className="flex items-center gap-2 text-sm">
                              <input
                                type="checkbox"
                                checked={useSearchContext}
                                onChange={(e) => setUseSearchContext(e.target.checked)}
                                className="rounded"
                              />
                              Use this context
                            </label>
                          </div>
                        </AlertDescription>
                      </Alert>
                    )}

                    <Textarea
                      placeholder="What would you like to know about your documents?"
                      value={question}
                      onChange={(e) => setQuestion(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleAskQuestion())}
                      className="min-h-24"
                    />

                    <div className="flex gap-2">
                      <Button className="flex-1" onClick={handleAskQuestion} disabled={isAsking || !question.trim()}>
                        {isAsking ? (
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        ) : (
                          <MessageSquare className="w-4 h-4 mr-2" />
                        )}
                        {isAsking ? 'Asking...' : 'Ask Question'}
                        {useSearchContext && (
                          <Badge variant="secondary" className="ml-2 text-xs">
                            Using Search Context
                          </Badge>
                        )}
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => {
                          if (searchContext) {
                            setUseSearchContext(!useSearchContext)
                          }
                        }}
                        disabled={!searchContext}
                      >
                        {useSearchContext ? "Remove Context" : "Use Previous Search"}
                      </Button>
                    </div>

                    {/* Search Strategy Options */}
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Search Strategy:</label>
                      <div className="grid grid-cols-3 gap-2 text-xs">
                        <Button
                          variant={searchStrategy === 'basic' ? "default" : "outline"}
                          size="sm"
                          onClick={() => setSearchStrategy('basic')}
                        >
                          Basic
                        </Button>
                        <Button
                          variant={searchStrategy === 'enhanced' ? "default" : "outline"}
                          size="sm"
                          onClick={() => setSearchStrategy('enhanced')}
                        >
                          Enhanced
                        </Button>
                        <Button
                          variant={searchStrategy === 'paragraph' ? "default" : "outline"}
                          size="sm"
                          onClick={() => setSearchStrategy('paragraph')}
                        >
                          Paragraph
                        </Button>
                      </div>
                    </div>

                    {/* Top-K Configuration */}
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Results to Retrieve (top_k):</label>
                      <div className="flex items-center gap-2">
                        <Input
                          type="number"
                          min="1"
                          max="50"
                          value={topK}
                          onChange={(e) => setTopK(Math.max(1, Math.min(50, parseInt(e.target.value) || 5)))}
                          className="w-20 text-sm"
                        />
                        <span className="text-xs text-slate-500">
                          Higher = more context, but slower & costlier
                        </span>
                      </div>
                      <div className="text-xs text-slate-400">
                        • 3-5: Focused answers (recommended)
                        • 8-12: Broad research  
                        • 15+: Comprehensive but expensive
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Answer Display */}
                {answer && (
                  <Card className="flex-1 min-h-0">
                    <CardHeader>
                      <CardTitle>Answer</CardTitle>
                      <CardDescription>AI-generated response with source citations</CardDescription>
                    </CardHeader>
                    <CardContent className="flex flex-col h-full">
                      <ScrollArea className="flex-1">
                        <div className="prose prose-slate max-w-none">
                          <ReactMarkdown 
                            remarkPlugins={[remarkGfm]}
                            components={{
                              p: ({node, ...props}) => <p className="mb-3 text-gray-700 leading-relaxed whitespace-pre-wrap" {...props} />,
                              h1: ({node, ...props}) => <h1 className="text-xl font-bold mb-3 text-gray-900 mt-4 first:mt-0" {...props} />,
                              h2: ({node, ...props}) => <h2 className="text-lg font-bold mb-3 text-gray-900 mt-4 first:mt-0" {...props} />,
                              h3: ({node, ...props}) => <h3 className="text-base font-bold mb-2 text-gray-900 mt-3 first:mt-0" {...props} />,
                              h4: ({node, ...props}) => <h4 className="text-base font-semibold mb-2 text-gray-900 mt-3 first:mt-0" {...props} />,
                              strong: ({node, ...props}) => <strong className="font-bold text-gray-900" {...props} />,
                              em: ({node, ...props}) => <em className="italic" {...props} />,
                              ul: ({node, ...props}) => <ul className="list-disc pl-6 mb-4 space-y-1" {...props} />,
                              ol: ({node, ...props}) => <ol className="list-decimal pl-6 mb-4 space-y-1" {...props} />,
                              li: ({node, ...props}) => <li className="text-gray-700" {...props} />,
                              code: ({node, ...props}) => <code className="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono" {...props} />,
                              pre: ({node, ...props}) => <pre className="bg-gray-100 p-3 rounded mb-4 text-sm overflow-x-auto" {...props} />,
                              blockquote: ({node, ...props}) => <blockquote className="border-l-4 border-gray-300 pl-4 italic text-gray-600 mb-4" {...props} />
                            }}
                          >
                            {answer}
                          </ReactMarkdown>
                        </div>
                        {answerSources.length > 0 && (
                          <div className="space-y-2">
                            <h4 className="font-medium text-sm">Sources:</h4>
                            <div className="flex flex-wrap gap-2">
                              {answerSources.map((source, index) => (
                                <Badge key={index} variant="outline" className="text-xs">
                                  {source}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                        {rawCitations.length > 0 && (
                          <div className="space-y-3 mt-4 pt-4 border-t border-slate-200">
                            <h4 className="font-medium text-sm flex items-center gap-2">
                              📖 Raw Citations ({rawCitations.length} excerpts)
                            </h4>
                            <div className="space-y-3">
                              {rawCitations.map((citation, index) => (
                                <div key={index} className="bg-slate-50 p-3 rounded-lg border">
                                  <div className="flex items-center gap-2 mb-2">
                                    <Badge variant="secondary" className="text-xs">
                                      {citation.collection}
                                    </Badge>
                                    <span className="text-xs text-slate-600">{citation.document}</span>
                                    {citation.relevancy_percentage && (
                                      <Badge variant="outline" className="text-xs ml-auto">
                                        {citation.relevancy_percentage}% relevant
                                      </Badge>
                                    )}
                                  </div>
                                  <div className="text-sm text-slate-700 bg-white p-2 rounded border-l-4 border-blue-200">
                                    {citation.text}
                                  </div>
                                  {citation.context && (
                                    <div className="text-xs text-slate-500 mt-1">
                                      Context: {citation.context}
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </ScrollArea>
                      <div className="flex justify-end mt-4 flex-shrink-0">
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => navigator.clipboard.writeText(answer)}
                        >
                          <Copy className="w-4 h-4 mr-2" />
                          Copy Answer
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>

              {/* Right Column: Answer Style & Context/History */}
              <div className="flex flex-col space-y-4">
                {/* Answer Style - Compact */}
                <Card className="flex-shrink-0">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm">Answer Style</CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="space-y-2">
                    <Textarea
                      value={systemPrompt}
                      onChange={(e) => setSystemPrompt(e.target.value)}
                      placeholder="Enter formatting instructions..."
                      className="min-h-[60px] text-xs resize-none"
                      rows={2}
                    />
                    <div className="flex gap-1 flex-wrap">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setSystemPrompt("Create a short brief summary at the top. Then reply your answer in Markdown.")}
                        className="text-xs h-6 px-2"
                      >
                        Default
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setSystemPrompt("Provide a detailed analysis with numbered sections and bullet points in Markdown format.")}
                        className="text-xs h-6 px-2"
                      >
                        Detailed
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setSystemPrompt("Give a concise, direct answer in plain text.")}
                        className="text-xs h-6 px-2"
                      >
                        Brief
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setSystemPrompt("")}
                        className="text-xs h-6 px-2"
                      >
                        Clear
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Context & History - Expandable */}
              <Card className="flex flex-col flex-1 min-h-0">
                <CardHeader className="flex-shrink-0">
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-base">Context & History ({conversationHistory.length})</CardTitle>
                      <CardDescription className="text-sm">Active context and previous questions</CardDescription>
                    </div>
                    {conversationHistory.length > 0 && (
                      <Button 
                        variant="outline" 
                        size="sm" 
                        onClick={() => setConversationHistory([])}
                        className="text-xs"
                      >
                        Clear History
                      </Button>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="flex flex-col h-full">
                  {/* Active Context */}
                  {useSearchContext && searchContext && (
                    <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg flex-shrink-0">
                      <h4 className="font-medium text-sm text-blue-800 mb-2">Active Search Context</h4>
                      <div className="space-y-1 text-xs text-blue-700">
                        <div>Query: "{searchContext.query}"</div>
                        <div>Results: {searchContext.results} chunks</div>
                        <div>Documents: {searchContext.documents.join(", ")}</div>
                        <div>Search ID: {lastSearchId || 'N/A'}</div>
                      </div>
                    </div>
                  )}

                  <ScrollArea className="flex-1 min-h-0">
                    <div className="space-y-3 text-sm">
                      {conversationHistory.length === 0 ? (
                        <div className="text-slate-500 text-center py-4">
                          No conversation history yet. Ask a question to get started!
                        </div>
                      ) : (
                        conversationHistory.slice().reverse().map((item, index) => (
                          <div 
                            key={index} 
                            className="p-2 bg-slate-50 rounded cursor-pointer transition-all duration-200 hover:bg-slate-100 hover:ring-2 hover:ring-blue-300 hover:shadow-sm"
                            onClick={() => {
                              setQuestion(item.question)
                              setAnswer(item.answer)
                              setAnswerSources(item.sources || [])
                            }}
                            title="Click to recall this question and answer"
                          >
                            <p className="font-medium">Q: {item.question}</p>
                            <p className="text-xs text-slate-700 mt-1 line-clamp-2">A: {item.answer.substring(0, 100)}...</p>
                            <p className="text-slate-600 text-xs mt-1">
                              {new Date(item.timestamp).toLocaleTimeString()} • 
                              {item.usedContext ? " Used search context" : " All documents"} • 
                              {item.searchStrategy} strategy
                            </p>
                          </div>
                        ))
                      )}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
              </div>
            </div>
          </TabsContent>

          {/* Status Tab */}
          <TabsContent value="status" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* System Health */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="w-5 h-5" />
                    System Health
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">ChromaDB</span>
                    <Badge variant={systemStatus?.chromadb === "connected" ? "default" : "destructive"}>
                      {systemStatus?.chromadb || 'unknown'}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">OpenAI</span>
                    <Badge variant={systemStatus?.openai === "connected" ? "default" : "destructive"}>
                      {systemStatus?.openai || 'unknown'}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">API Status</span>
                    <Badge variant={systemStatus?.api === "healthy" ? "default" : "destructive"}>
                      {systemStatus?.api || 'unknown'}
                    </Badge>
                  </div>
                </CardContent>
              </Card>

              {/* Document Statistics */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Database className="w-5 h-5" />
                    Document Stats
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Total Documents</span>
                    <Badge variant="outline">{systemStatus?.documents || 0}</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Collections</span>
                    <Badge variant="outline">{systemStatus?.collections || 0}</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Total Chunks</span>
                    <Badge variant="outline">{Object.values(documents).reduce((sum, doc) => sum + doc.total_chunks, 0)}</Badge>
                  </div>
                </CardContent>
              </Card>

              {/* Performance Metrics */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Server className="w-5 h-5" />
                    Performance
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span>Memory Usage</span>
                      <span>68%</span>
                    </div>
                    <Progress value={68} className="h-2" />
                  </div>
                  <div className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span>CPU Usage</span>
                      <span>23%</span>
                    </div>
                    <Progress value={23} className="h-2" />
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Avg Response Time</span>
                    <Badge variant="outline">1.2s</Badge>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Collections Detail */}
            <Card>
              <CardHeader>
                <CardTitle>Collection Details</CardTitle>
                <CardDescription>Detailed view of document collections and their contents</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="border rounded-lg p-4">
                      <h4 className="font-medium mb-2">original_texts</h4>
                      <p className="text-sm text-slate-600 mb-2">Raw document chunks</p>
                      <div className="flex justify-between text-sm">
                        <span>Items: 89</span>
                        <span>Documents: 3</span>
                      </div>
                    </div>
                    <div className="border rounded-lg p-4">
                      <h4 className="font-medium mb-2">summaries</h4>
                      <p className="text-sm text-slate-600 mb-2">Generated summaries</p>
                      <div className="flex justify-between text-sm">
                        <span>Items: 46</span>
                        <span>Documents: 2</span>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

