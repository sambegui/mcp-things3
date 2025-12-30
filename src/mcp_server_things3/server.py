import asyncio
import logging
import subprocess
import sys
from urllib.parse import quote

import mcp.types as types
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio

# Handle both relative and absolute imports
try:
    from .applescript_handler import AppleScriptHandler
except ImportError:
    from applescript_handler import AppleScriptHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the server
server = Server("mcp-server-things3")

class XCallbackURLHandler:
    """Handles x-callback-url execution for Things3."""

    @staticmethod
    def build_url(base_url: str, params: dict) -> str:
        """
        Builds a properly encoded x-callback-url.
        """
        if not params:
            return base_url
        
        encoded_params = []
        for key, value in params.items():
            if value is not None:
                # Handle list values (like tags)
                if isinstance(value, list):
                    value = ",".join(str(v) for v in value)
                # Use quote() instead of quote_plus() - Things3 prefers %20 over +
                encoded_params.append(f"{key}={quote(str(value), safe='')}")
        
        return f"{base_url}?{'&'.join(encoded_params)}"

    @staticmethod
    def call_url(url: str) -> str:
        """
        Executes an x-callback-url using the 'open' command.
        """
        try:
            result = subprocess.run(
                ['open', url],
                check=True,
                capture_output=True,
                text=True
            )
            return result.stdout
        except FileNotFoundError:
            logger.error("'open' command not found")
            raise RuntimeError("Failed to execute x-callback-url: 'open' command not found")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to execute x-callback-url: {e}")
            raise RuntimeError(f"Failed to execute x-callback-url: {e}")
    
    @staticmethod
    def validate_things3_available() -> bool:
        """
        Check if Things3 is available on the system.
        """
        try:
            result = subprocess.run(
                ['osascript', '-e', 'tell application "System Events" to exists application process "Things3"'],
                check=True,
                capture_output=True,
                text=True
            )
            return result.stdout.strip() == "true"
        except subprocess.CalledProcessError:
            return False

    @staticmethod
    def build_show_url(view: str, name: str | None = None, filter_tags: list[str] | None = None) -> str:
        """
        Build a things:///show URL to navigate to a specific view in Things 3.

        Args:
            view: The view to show. Predefined list IDs: inbox, today, upcoming, anytime,
                  someday, logbook, tomorrow, deadlines, repeating, all-projects.
                  Or 'project'/'tag' to use the name parameter.
            name: For 'project' or 'tag' views, the name of the item to show.
            filter_tags: Optional list of tag names to filter the view.

        Returns:
            The constructed things:///show URL.
        """
        base_url = "things:///show"
        params = {}

        # Built-in list IDs that use the id parameter directly
        builtin_list_ids = {
            "inbox", "today", "upcoming", "anytime", "someday",
            "logbook", "tomorrow", "deadlines", "repeating", "all-projects"
        }

        if view in builtin_list_ids:
            # Direct list ID
            params["id"] = view
        elif view in ("project", "tag"):
            # Use query parameter to find by name
            if name:
                params["query"] = name
            else:
                # Fall back to showing relevant list
                params["id"] = "all-projects" if view == "project" else "anytime"
        else:
            # Treat unknown view as a direct ID (could be a UUID)
            params["id"] = view

        # Add tag filter if provided
        if filter_tags:
            params["filter"] = ",".join(filter_tags)

        return XCallbackURLHandler.build_url(base_url, params)

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available Things3 tools.
    """
    return [
        types.Tool(
            name="view-inbox",
            description="View all todos in the Things3 inbox",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            },
        ),
        types.Tool(
            name="view-projects",
            description="View all projects in Things3",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            },
        ),
        types.Tool(
            name="view-todos",
            description="View all todos in Things3",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            },
        ),
        types.Tool(
            name="create-things3-project",
            description="Create a new project in Things3",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "notes": {"type": "string"},
                    "area": {"type": "string"},
                    "when": {"type": "string"},
                    "deadline": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["title"]
            },
        ),
        types.Tool(
            name="create-things3-todo",
            description="Create a new to-do in Things3 with optional reminder time",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "The title of the to-do"},
                    "notes": {"type": "string", "description": "Notes for the to-do"},
                    "when": {"type": "string", "description": "When to schedule: 'today', 'tomorrow', 'evening', 'anytime', 'someday', or date string. Add @TIME for reminder (e.g., 'today@10am', 'tomorrow@2:30pm', '2025-01-15@9am')"},
                    "deadline": {"type": "string", "description": "Due date in YYYY-MM-DD format"},
                    "checklist": {"type": "array", "items": {"type": "string"}, "description": "Checklist items"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags to apply"},
                    "list": {"type": "string", "description": "Project or area to add to"},
                    "heading": {"type": "string", "description": "Heading within a project"},
                },
                "required": ["title"]
            },
        ),
        types.Tool(
            name="complete-things3-todo",
            description="Mark a Things3 todo as completed by searching for its title",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "The title or partial title of the todo to complete"},
                },
                "required": ["title"]
            },
        ),
        types.Tool(
            name="search-things3-todos",
            description="Search for todos in Things3 by title or content",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search term to look for in todo titles and notes"},
                },
                "required": ["query"]
            },
        ),
        # ===========================================
        # T013-T017: User Story 1 - View Tools
        # ===========================================
        types.Tool(
            name="view-logbook",
            description="View recently completed tasks from the Things3 logbook with completion dates",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of tasks to return (default: 50, max: 200)",
                        "default": 50
                    },
                    "days": {
                        "type": "integer",
                        "description": "Only return tasks completed within this many days (default: 7)",
                        "default": 7
                    }
                },
                "additionalProperties": False
            },
        ),
        types.Tool(
            name="view-by-tag",
            description="View all tasks with a specific tag across all lists and projects",
            inputSchema={
                "type": "object",
                "properties": {
                    "tag": {
                        "type": "string",
                        "description": "The tag name to filter by (must exist in Things3)"
                    },
                    "include_completed": {
                        "type": "boolean",
                        "description": "Include completed tasks in results (default: false)",
                        "default": False
                    }
                },
                "required": ["tag"],
                "additionalProperties": False
            },
        ),
        types.Tool(
            name="view-overdue",
            description="View all tasks that have passed their deadline (due date before today)",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            },
        ),
        # ===========================================
        # T027-T029: User Story 2 - Statistics Tools
        # ===========================================
        types.Tool(
            name="task-counts",
            description="Get quick task count statistics across all Things3 lists (inbox, today, upcoming, anytime, someday, logbook)",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            },
        ),
        types.Tool(
            name="weekly-review",
            description="Generate a comprehensive weekly review summary for GTD workflow including: overdue tasks, inbox staleness, completion stats, and someday items to review",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days to analyze for completion stats (default: 7)",
                        "default": 7
                    },
                    "stale_days": {
                        "type": "integer",
                        "description": "Consider inbox items stale after this many days (default: 7)",
                        "default": 7
                    },
                    "someday_review_days": {
                        "type": "integer",
                        "description": "Suggest reviewing someday items older than this many days (default: 30)",
                        "default": 30
                    }
                },
                "additionalProperties": False
            },
        ),
        # ===========================================
        # T031-T032: User Story 3 - Quick Add Tool
        # ===========================================
        types.Tool(
            name="quick-add",
            description="Ultra-simple task creation - quickly add a task to the inbox with just a title. For tasks with notes, deadlines, tags, or other metadata, use create-things3-todo instead.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The task title (required)",
                        "minLength": 1,
                        "maxLength": 500
                    }
                },
                "required": ["title"],
                "additionalProperties": False
            },
        ),
        # ===========================================
        # T038-T040: User Story 4 - State Management Tools
        # ===========================================
        types.Tool(
            name="cancel-todo",
            description="Cancel/abandon a task by its title. If multiple tasks match, returns the matches for clarification.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The title or partial title of the task to cancel"
                    }
                },
                "required": ["title"],
                "additionalProperties": False
            },
        ),
        types.Tool(
            name="reschedule-todo",
            description="Reschedule a task to a new date. Supports natural language dates like 'tomorrow', 'next week', 'next monday', or YYYY-MM-DD format.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The title or partial title of the task to reschedule"
                    },
                    "when": {
                        "type": "string",
                        "description": "New date: 'today', 'tomorrow', 'next week', 'next monday', 'someday', 'anytime', or 'YYYY-MM-DD'"
                    }
                },
                "required": ["title", "when"],
                "additionalProperties": False
            },
        ),
        types.Tool(
            name="bulk-complete",
            description="Complete multiple tasks at once by their titles. Returns results for each task.",
            inputSchema={
                "type": "object",
                "properties": {
                    "titles": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of task titles to complete",
                        "minItems": 1,
                        "maxItems": 20
                    }
                },
                "required": ["titles"],
                "additionalProperties": False
            },
        ),
        # ===========================================
        # T045: User Story 5 - Navigation Tool
        # ===========================================
        types.Tool(
            name="show-in-things",
            description="Open Things 3 and navigate to a specific view, project, or tag. Useful for transitioning from AI conversation to the full Things 3 interface.",
            inputSchema={
                "type": "object",
                "properties": {
                    "view": {
                        "type": "string",
                        "description": "The view to open. Use list names for built-in views, or 'project'/'tag' for named items.",
                        "enum": [
                            "inbox",
                            "today",
                            "upcoming",
                            "anytime",
                            "someday",
                            "logbook",
                            "tomorrow",
                            "deadlines",
                            "all-projects",
                            "project",
                            "tag"
                        ]
                    },
                    "name": {
                        "type": "string",
                        "description": "Required when view is 'project' or 'tag'. The name of the project or tag to open."
                    },
                    "filter_tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional: Filter the view by these tag names"
                    }
                },
                "required": ["view"],
                "additionalProperties": False
            },
        ),
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests.
    """
    try:
        if name == "view-inbox":
            # Validate Things3 is accessible
            if not AppleScriptHandler.validate_things3_access():
                return [types.TextContent(type="text", text="Things3 is not available. Please ensure Things3 is installed and running.")]
            
            try:
                todos = AppleScriptHandler.get_inbox_tasks() or []
                if not todos:
                    return [types.TextContent(type="text", text="No todos found in Things3 inbox.")]

                response = ["Todos in Things3 inbox:"]
                for todo in todos:
                    title = (todo.get("title", "Untitled Todo")).strip()
                    due_date = todo.get("due_date", "No Due Date")
                    when_date = todo.get("when", "No Scheduled Date")
                    response.append(f"\n• {title} (Due: {due_date}, When: {when_date})")

                return [types.TextContent(type="text", text="\n".join(response))]
            except Exception as e:
                logger.error(f"Error retrieving inbox tasks: {e}")
                return [types.TextContent(type="text", text=f"Failed to retrieve inbox tasks: {str(e)}")]

        if name == "view-projects":
            # Validate Things3 is accessible
            if not AppleScriptHandler.validate_things3_access():
                return [types.TextContent(type="text", text="Things3 is not available. Please ensure Things3 is installed and running.")]
            
            try:
                projects = AppleScriptHandler.get_projects() or []
                if not projects:
                    return [types.TextContent(type="text", text="No projects found in Things3.")]

                response = ["Projects in Things3:"]
                for project in projects:
                    title = (project.get("title", "Untitled Project")).strip()
                    response.append(f"\n• {title}")

                return [types.TextContent(type="text", text="\n".join(response))]
            except Exception as e:
                logger.error(f"Error retrieving projects: {e}")
                return [types.TextContent(type="text", text=f"Failed to retrieve projects: {str(e)}")]

        if name == "view-todos":
            # Validate Things3 is accessible
            if not AppleScriptHandler.validate_things3_access():
                return [types.TextContent(type="text", text="Things3 is not available. Please ensure Things3 is installed and running.")]
            
            try:
                todos = AppleScriptHandler.get_todays_tasks() or []
                if not todos:
                    return [types.TextContent(type="text", text="No todos found in Things3.")]

                response = ["Todos in Things3:"]
                for todo in todos:
                    title = (todo.get("title", "Untitled Todo")).strip()
                    due_date = todo.get("due_date", "No Due Date")
                    when_date = todo.get("when", "No Scheduled Date")
                    response.append(f"\n• {title} (Due: {due_date}, When: {when_date})")

                return [types.TextContent(type="text", text="\n".join(response))]
            except Exception as e:
                logger.error(f"Error retrieving todos: {e}")
                return [types.TextContent(type="text", text=f"Failed to retrieve todos: {str(e)}")]

        if name == "create-things3-project":
            if not arguments:
                raise ValueError("Missing arguments")

            # Validate Things3 is available
            if not XCallbackURLHandler.validate_things3_available():
                return [
                    types.TextContent(
                        type="text",
                        text="Things3 is not running or not installed. Please start Things3 and try again.",
                    )
                ]

            # Build the Things3 URL with proper encoding
            base_url = "things:///add-project"
            params = {
                "title": arguments["title"]
            }
            
            # Optional parameters
            if "notes" in arguments:
                params["notes"] = arguments["notes"]
            if "area" in arguments:
                params["area"] = arguments["area"]
            if "when" in arguments:
                params["when"] = arguments["when"]
            if "deadline" in arguments:
                params["deadline"] = arguments["deadline"]
            if "tags" in arguments:
                params["tags"] = arguments["tags"]
            
            url = XCallbackURLHandler.build_url(base_url, params)
            logger.info(f"Creating project with URL: {url}")
            
            try:
                XCallbackURLHandler.call_url(url)
                return [
                    types.TextContent(
                        type="text",
                        text=f"Created project '{arguments['title']}' in Things3",
                    )
                ]
            except Exception as e:
                logger.error(f"Error creating project: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Failed to create project in Things3: {str(e)}",
                    )
                ]

        if name == "create-things3-todo":
            if not arguments:
                raise ValueError("Missing arguments")

            # Validate Things3 is available
            if not XCallbackURLHandler.validate_things3_available():
                return [
                    types.TextContent(
                        type="text",
                        text="Things3 is not running or not installed. Please start Things3 and try again.",
                    )
                ]

            # Build the Things3 URL with proper encoding
            base_url = "things:///add"
            params = {
                "title": arguments["title"]
            }
            
            # Optional parameters
            if "notes" in arguments:
                params["notes"] = arguments["notes"]
            if "when" in arguments:
                params["when"] = arguments["when"]
            if "deadline" in arguments:
                params["deadline"] = arguments["deadline"]
            if "checklist" in arguments:
                params["checklist"] = "\n".join(arguments["checklist"])
            if "tags" in arguments:
                params["tags"] = arguments["tags"]
            if "list" in arguments:
                params["list"] = arguments["list"]
            if "heading" in arguments:
                params["heading"] = arguments["heading"]
            
            url = XCallbackURLHandler.build_url(base_url, params)
            logger.info(f"Creating todo with URL: {url}")
            
            try:
                XCallbackURLHandler.call_url(url)
                return [
                    types.TextContent(
                        type="text",
                        text=f"Created to-do '{arguments['title']}' in Things3",
                    )
                ]
            except Exception as e:
                logger.error(f"Error creating todo: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Failed to create to-do in Things3: {str(e)}",
                    )
                ]

        if name == "complete-things3-todo":
            if not arguments:
                raise ValueError("Missing arguments")

            # Validate Things3 is available
            if not AppleScriptHandler.validate_things3_access():
                return [
                    types.TextContent(
                        type="text",
                        text="Things3 is not available. Please ensure Things3 is installed and running.",
                    )
                ]

            try:
                success = AppleScriptHandler.complete_todo_by_title(arguments["title"])
                if success:
                    return [
                        types.TextContent(
                            type="text",
                            text=f"Successfully completed todo containing '{arguments['title']}'",
                        )
                    ]
                else:
                    return [
                        types.TextContent(
                            type="text",
                            text=f"No incomplete todo found containing '{arguments['title']}'",
                        )
                    ]
            except Exception as e:
                logger.error(f"Error completing todo: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Failed to complete todo: {str(e)}",
                    )
                ]

        if name == "search-things3-todos":
            if not arguments:
                raise ValueError("Missing arguments")

            # Validate Things3 is available
            if not AppleScriptHandler.validate_things3_access():
                return [
                    types.TextContent(
                        type="text",
                        text="Things3 is not available. Please ensure Things3 is installed and running.",
                    )
                ]

            try:
                todos = AppleScriptHandler.search_todos(arguments["query"])
                if not todos:
                    return [
                        types.TextContent(
                            type="text",
                            text=f"No todos found matching '{arguments['query']}'",
                        )
                    ]

                response = [f"Found {len(todos)} todo(s) matching '{arguments['query']}':"]
                for todo in todos:
                    title = todo.get("title", "Untitled Todo")
                    status = todo.get("status", "unknown")
                    status_icon = "✅" if status == "completed" else "⏳"
                    due_date = todo.get("due_date", "No Due Date")
                    response.append(f"\n{status_icon} {title} (Due: {due_date})")

                return [types.TextContent(type="text", text="\n".join(response))]
            except Exception as e:
                logger.error(f"Error searching todos: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Failed to search todos: {str(e)}",
                    )
                ]

        # ===========================================
        # T018-T022: User Story 1 - View Tool Handlers
        # ===========================================

        if name == "view-logbook":
            if not AppleScriptHandler.validate_things3_access():
                return [types.TextContent(type="text", text="Things3 is not available. Please ensure Things3 is installed and running.")]

            try:
                limit = (arguments or {}).get("limit", 50)
                days = (arguments or {}).get("days", 7)

                # Enforce limits
                limit = min(max(1, limit), 200)
                days = min(max(1, days), 365)

                tasks = AppleScriptHandler.get_logbook_tasks(limit=limit, days=days)

                if not tasks:
                    return [types.TextContent(type="text", text=f"No completed tasks found in the last {days} days.")]

                response = [f"Completed tasks (last {days} days, showing {len(tasks)}):"]
                for task in tasks:
                    title = task.get("title", "Untitled")
                    completion = task.get("completion_date", "")
                    project = task.get("project", "")
                    line = f"\n✅ {title}"
                    if completion:
                        line += f" (Completed: {completion})"
                    if project:
                        line += f" [Project: {project}]"
                    response.append(line)

                return [types.TextContent(type="text", text="".join(response))]
            except Exception as e:
                logger.error(f"Error viewing logbook: {e}")
                return [types.TextContent(type="text", text=f"Failed to retrieve logbook: {str(e)}")]

        if name == "view-by-tag":
            if not arguments or "tag" not in arguments:
                return [types.TextContent(type="text", text="Missing required parameter: tag")]

            if not AppleScriptHandler.validate_things3_access():
                return [types.TextContent(type="text", text="Things3 is not available. Please ensure Things3 is installed and running.")]

            try:
                tag_name = arguments["tag"]
                include_completed = arguments.get("include_completed", False)

                tasks = AppleScriptHandler.get_tasks_by_tag(tag_name, include_completed)

                if not tasks:
                    return [types.TextContent(type="text", text=f"No tasks found with tag '{tag_name}'. Make sure the tag exists in Things3.")]

                response = [f"Tasks tagged '{tag_name}' ({len(tasks)} found):"]
                for task in tasks:
                    title = task.get("title", "Untitled")
                    status = task.get("status", "open")
                    status_icon = "✅" if status == "completed" else "⏳"
                    due_date = task.get("due_date", "")
                    project = task.get("project", "")
                    line = f"\n{status_icon} {title}"
                    if due_date:
                        line += f" (Due: {due_date})"
                    if project:
                        line += f" [Project: {project}]"
                    response.append(line)

                return [types.TextContent(type="text", text="".join(response))]
            except Exception as e:
                logger.error(f"Error viewing tasks by tag: {e}")
                return [types.TextContent(type="text", text=f"Failed to retrieve tasks by tag: {str(e)}")]

        if name == "view-overdue":
            if not AppleScriptHandler.validate_things3_access():
                return [types.TextContent(type="text", text="Things3 is not available. Please ensure Things3 is installed and running.")]

            try:
                tasks = AppleScriptHandler.get_overdue_tasks()

                if not tasks:
                    return [types.TextContent(type="text", text="No overdue tasks found. You're all caught up!")]

                response = [f"⚠️ Overdue Tasks ({len(tasks)}):"]
                for task in tasks:
                    title = task.get("title", "Untitled")
                    due_date = task.get("due_date", "")
                    days_overdue = task.get("days_overdue", 0)
                    project = task.get("project", "")
                    line = f"\n🔴 {title} - {days_overdue} day{'s' if days_overdue != 1 else ''} overdue"
                    if due_date:
                        line += f" (Due: {due_date})"
                    if project:
                        line += f" [Project: {project}]"
                    response.append(line)

                return [types.TextContent(type="text", text="".join(response))]
            except Exception as e:
                logger.error(f"Error viewing overdue tasks: {e}")
                return [types.TextContent(type="text", text=f"Failed to retrieve overdue tasks: {str(e)}")]

        # ===========================================
        # T028-T030: User Story 2 - Statistics Tool Handlers
        # ===========================================

        if name == "task-counts":
            if not AppleScriptHandler.validate_things3_access():
                return [types.TextContent(type="text", text="Things3 is not available. Please ensure Things3 is installed and running.")]

            try:
                counts = AppleScriptHandler.get_task_counts()

                if not counts:
                    return [types.TextContent(type="text", text="Failed to retrieve task counts.")]

                response = ["📊 Task Counts:"]
                response.append(f"\n  📥 Inbox: {counts.get('inbox', 0)}")
                response.append(f"\n  📅 Today: {counts.get('today', 0)}")
                response.append(f"\n  🔜 Upcoming: {counts.get('upcoming', 0)}")
                response.append(f"\n  ⭐ Anytime: {counts.get('anytime', 0)}")
                response.append(f"\n  💭 Someday: {counts.get('someday', 0)}")
                response.append(f"\n  ✅ Logbook: {counts.get('logbook', 0)}")
                response.append(f"\n\n  📋 Total Open: {counts.get('total_open', 0)}")

                return [types.TextContent(type="text", text="".join(response))]
            except Exception as e:
                logger.error(f"Error getting task counts: {e}")
                return [types.TextContent(type="text", text=f"Failed to get task counts: {str(e)}")]

        if name == "weekly-review":
            if not AppleScriptHandler.validate_things3_access():
                return [types.TextContent(type="text", text="Things3 is not available. Please ensure Things3 is installed and running.")]

            try:
                days = (arguments or {}).get("days", 7)
                stale_days = (arguments or {}).get("stale_days", 7)
                someday_review_days = (arguments or {}).get("someday_review_days", 30)

                # Gather all data
                overdue_tasks = AppleScriptHandler.get_overdue_tasks()
                inbox_tasks = AppleScriptHandler.get_inbox_with_ages()
                completion_stats = AppleScriptHandler.get_completion_stats(days)
                someday_tasks = AppleScriptHandler.get_someday_with_ages()
                task_counts = AppleScriptHandler.get_task_counts()

                # Calculate inbox staleness
                stale_inbox = [t for t in inbox_tasks if t.get("age_days", 0) >= stale_days]
                oldest_inbox_days = max([t.get("age_days", 0) for t in inbox_tasks], default=0)

                # Filter someday items for review
                someday_for_review = [t for t in someday_tasks if t.get("age_days", 0) >= someday_review_days]

                # Build the weekly review report
                from datetime import datetime
                response = [f"📋 Weekly Review Summary"]
                response.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
                response.append("\n" + "=" * 40)

                # Overdue Section
                response.append(f"\n\n⚠️ OVERDUE TASKS ({len(overdue_tasks)})")
                if overdue_tasks:
                    for task in overdue_tasks[:5]:  # Show top 5
                        title = task.get("title", "Untitled")
                        days_overdue = task.get("days_overdue", 0)
                        response.append(f"\n  🔴 {title} ({days_overdue} day{'s' if days_overdue != 1 else ''} overdue)")
                    if len(overdue_tasks) > 5:
                        response.append(f"\n  ... and {len(overdue_tasks) - 5} more")
                else:
                    response.append("\n  ✅ None - you're caught up!")

                # Inbox Section
                response.append(f"\n\n📥 INBOX STATUS ({len(inbox_tasks)} items)")
                response.append(f"\n  Total items: {len(inbox_tasks)}")
                response.append(f"\n  Stale items (>{stale_days} days): {len(stale_inbox)}")
                if oldest_inbox_days > 0:
                    response.append(f"\n  Oldest item: {oldest_inbox_days} days")
                if stale_inbox:
                    response.append("\n  Stale items to process:")
                    for task in stale_inbox[:3]:
                        title = task.get("title", "Untitled")
                        age = task.get("age_days", 0)
                        response.append(f"\n    • {title} ({age} days)")
                    if len(stale_inbox) > 3:
                        response.append(f"\n    ... and {len(stale_inbox) - 3} more")

                # Completion Stats
                response.append(f"\n\n✅ COMPLETION STATS (last {days} days)")
                response.append(f"\n  Completed this period: {completion_stats.get('completed_period', 0)}")
                response.append(f"\n  Completed today: {completion_stats.get('completed_today', 0)}")

                # Overall Counts
                response.append(f"\n\n📊 CURRENT COUNTS")
                response.append(f"\n  Today: {task_counts.get('today', 0)}")
                response.append(f"\n  Upcoming: {task_counts.get('upcoming', 0)}")
                response.append(f"\n  Anytime: {task_counts.get('anytime', 0)}")
                response.append(f"\n  Total Open: {task_counts.get('total_open', 0)}")

                # Someday Review
                response.append(f"\n\n💭 SOMEDAY REVIEW ({len(someday_tasks)} total)")
                if someday_for_review:
                    response.append(f"\n  Items to review (>{someday_review_days} days old): {len(someday_for_review)}")
                    for task in someday_for_review[:5]:
                        title = task.get("title", "Untitled")
                        age = task.get("age_days", 0)
                        response.append(f"\n    • {title} ({age} days)")
                    if len(someday_for_review) > 5:
                        response.append(f"\n    ... and {len(someday_for_review) - 5} more")
                else:
                    response.append("\n  No items need review yet")

                response.append("\n\n" + "=" * 40)
                response.append("\n📌 Action Items:")
                action_count = 0
                if overdue_tasks:
                    response.append(f"\n  1. Process {len(overdue_tasks)} overdue task{'s' if len(overdue_tasks) != 1 else ''}")
                    action_count += 1
                if stale_inbox:
                    response.append(f"\n  {action_count + 1}. Clear {len(stale_inbox)} stale inbox item{'s' if len(stale_inbox) != 1 else ''}")
                    action_count += 1
                if someday_for_review:
                    response.append(f"\n  {action_count + 1}. Review {len(someday_for_review)} old someday item{'s' if len(someday_for_review) != 1 else ''}")
                if action_count == 0 and not someday_for_review:
                    response.append("\n  ✅ Great job! No urgent actions needed.")

                return [types.TextContent(type="text", text="".join(response))]
            except Exception as e:
                logger.error(f"Error generating weekly review: {e}")
                return [types.TextContent(type="text", text=f"Failed to generate weekly review: {str(e)}")]

        # ===========================================
        # T033: User Story 3 - Quick Add Handler
        # ===========================================

        if name == "quick-add":
            if not arguments or "title" not in arguments:
                return [types.TextContent(type="text", text="Missing required parameter: title")]

            if not XCallbackURLHandler.validate_things3_available():
                return [types.TextContent(type="text", text="Things3 is not running or not installed. Please start Things3 and try again.")]

            try:
                title = arguments["title"].strip()
                if not title:
                    return [types.TextContent(type="text", text="Title cannot be empty.")]

                # Build simple add URL - just title, goes to inbox
                url = XCallbackURLHandler.build_url("things:///add", {"title": title})
                logger.info(f"Quick-add task with URL: {url}")

                XCallbackURLHandler.call_url(url)

                return [types.TextContent(
                    type="text",
                    text=f"✅ Added to inbox: \"{title}\""
                )]
            except Exception as e:
                logger.error(f"Error quick-adding task: {e}")
                return [types.TextContent(type="text", text=f"Failed to add task: {str(e)}")]

        # ===========================================
        # T041-T043: User Story 4 - State Management Handlers
        # ===========================================

        if name == "cancel-todo":
            if not arguments or "title" not in arguments:
                return [types.TextContent(type="text", text="Missing required parameter: title")]

            if not AppleScriptHandler.validate_things3_access():
                return [types.TextContent(type="text", text="Things3 is not available. Please ensure Things3 is installed and running.")]

            try:
                title = arguments["title"]
                result = AppleScriptHandler.cancel_todo_by_title(title)

                if result["status"] == "success":
                    return [types.TextContent(
                        type="text",
                        text=f"❌ Canceled: \"{result['title']}\""
                    )]
                elif result["status"] == "not_found":
                    return [types.TextContent(type="text", text=result["message"])]
                elif result["status"] == "ambiguous":
                    matches = result.get("matches", [])
                    response = [f"⚠️ {result['message']}"]
                    response.append("\n\nMatching tasks:")
                    for match in matches[:10]:
                        match_title = match.get("title", "Untitled")
                        project = match.get("project", "")
                        line = f"\n  • {match_title}"
                        if project:
                            line += f" [Project: {project}]"
                        response.append(line)
                    response.append("\n\nPlease provide a more specific title.")
                    return [types.TextContent(type="text", text="".join(response))]
                else:
                    return [types.TextContent(type="text", text=f"Error: {result.get('message', 'Unknown error')}")]
            except Exception as e:
                logger.error(f"Error canceling task: {e}")
                return [types.TextContent(type="text", text=f"Failed to cancel task: {str(e)}")]

        if name == "reschedule-todo":
            if not arguments or "title" not in arguments or "when" not in arguments:
                return [types.TextContent(type="text", text="Missing required parameters: title and when")]

            if not AppleScriptHandler.validate_things3_access():
                return [types.TextContent(type="text", text="Things3 is not available. Please ensure Things3 is installed and running.")]

            try:
                title = arguments["title"]
                when = arguments["when"]
                result = AppleScriptHandler.reschedule_todo_by_title(title, when)

                if result["status"] == "success":
                    return [types.TextContent(
                        type="text",
                        text=f"📅 Rescheduled \"{result['title']}\" to {result['scheduled_to']}"
                    )]
                elif result["status"] == "not_found":
                    return [types.TextContent(type="text", text=result["message"])]
                elif result["status"] == "ambiguous":
                    matches = result.get("matches", [])
                    response = [f"⚠️ {result['message']}"]
                    response.append("\n\nMatching tasks:")
                    for match in matches[:10]:
                        match_title = match.get("title", "Untitled")
                        project = match.get("project", "")
                        line = f"\n  • {match_title}"
                        if project:
                            line += f" [Project: {project}]"
                        response.append(line)
                    response.append("\n\nPlease provide a more specific title.")
                    return [types.TextContent(type="text", text="".join(response))]
                else:
                    return [types.TextContent(type="text", text=f"Error: {result.get('message', 'Unknown error')}")]
            except Exception as e:
                logger.error(f"Error rescheduling task: {e}")
                return [types.TextContent(type="text", text=f"Failed to reschedule task: {str(e)}")]

        if name == "bulk-complete":
            if not arguments or "titles" not in arguments:
                return [types.TextContent(type="text", text="Missing required parameter: titles")]

            if not AppleScriptHandler.validate_things3_access():
                return [types.TextContent(type="text", text="Things3 is not available. Please ensure Things3 is installed and running.")]

            try:
                titles = arguments["titles"]
                if not titles:
                    return [types.TextContent(type="text", text="No task titles provided.")]

                result = AppleScriptHandler.bulk_complete_todos(titles)

                response = [f"📋 Bulk Complete Results:"]
                response.append(f"\n  Requested: {result['requested']}")
                response.append(f"\n  Succeeded: {result['succeeded']}")
                response.append(f"\n  Failed: {result['failed']}")
                response.append("\n\nDetails:")

                for item in result.get("results", []):
                    title = item.get("title", "Unknown")
                    status = item.get("status", "unknown")
                    if status == "success":
                        response.append(f"\n  ✅ {title}")
                    elif status == "ambiguous":
                        response.append(f"\n  ⚠️ {title} - multiple matches found")
                    elif status == "not_found":
                        response.append(f"\n  ❓ {title} - not found")
                    else:
                        error = item.get("error", "Unknown error")
                        response.append(f"\n  ❌ {title} - {error}")

                return [types.TextContent(type="text", text="".join(response))]
            except Exception as e:
                logger.error(f"Error bulk completing tasks: {e}")
                return [types.TextContent(type="text", text=f"Failed to bulk complete tasks: {str(e)}")]

        # ===========================================
        # T046: User Story 5 - Navigation Handler
        # ===========================================

        if name == "show-in-things":
            if not arguments or "view" not in arguments:
                return [types.TextContent(type="text", text="Missing required parameter: view")]

            try:
                view = arguments["view"]
                item_name = arguments.get("name")
                filter_tags = arguments.get("filter_tags")

                # Validate that name is provided for project/tag views
                if view in ("project", "tag") and not item_name:
                    return [types.TextContent(
                        type="text",
                        text=f"When view is '{view}', you must provide a 'name' parameter."
                    )]

                # Build the show URL
                url = XCallbackURLHandler.build_show_url(view, item_name, filter_tags)
                logger.info(f"Opening Things 3 with URL: {url}")

                # Execute the URL to open Things 3
                XCallbackURLHandler.call_url(url)

                # Build response message
                if view in ("project", "tag"):
                    opened_desc = f"{view.capitalize()}: {item_name}"
                else:
                    # Map view IDs to human-readable names
                    view_names = {
                        "inbox": "Inbox",
                        "today": "Today",
                        "upcoming": "Upcoming",
                        "anytime": "Anytime",
                        "someday": "Someday",
                        "logbook": "Logbook",
                        "tomorrow": "Tomorrow",
                        "deadlines": "Deadlines",
                        "all-projects": "All Projects"
                    }
                    opened_desc = view_names.get(view, view.replace("-", " ").title())

                message = f"📱 Opened Things 3 to: {opened_desc}"
                if filter_tags:
                    message += f" (filtered by: {', '.join(filter_tags)})"

                return [types.TextContent(type="text", text=message)]
            except Exception as e:
                logger.error(f"Error showing Things 3 view: {e}")
                return [types.TextContent(type="text", text=f"Failed to open Things 3: {str(e)}")]

        raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        logger.error(f"Error handling tool {name}: {e}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    """Run the server."""
    logger.info("Starting Things3 MCP server...")
    
    # Handle graceful shutdown
    def handle_signal(signum, frame):
        logger.info("Shutting down gracefully...")
        raise SystemExit(0)

    import signal
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    # Run the server using stdin/stdout streams
    try:
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="mcp-server-things3",
                    server_version="0.2.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
    except SystemExit:
        pass
    except Exception as e:
        logger.error(f"Server error: {e}")
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def run():
    """Entry point for the CLI command."""
    asyncio.run(main())


if __name__ == "__main__":
    run()