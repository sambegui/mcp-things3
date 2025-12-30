[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/drjforrest-mcp-things3-badge.png)](https://mseep.ai/app/drjforrest-mcp-things3)

# MCP Server for Things3

A robust MCP (Model Context Protocol) server providing comprehensive integration with Things3, allowing you to create, manage, and search tasks and projects through the MCP protocol. Features improved error handling, secure URL encoding, and enhanced AppleScript integration.

## Features

### Core Operations
- **Create Projects**: Create new projects in Things3 with full metadata support
- **Create Todos**: Create new to-dos with detailed properties including checklists, tags, and dates
- **Complete Tasks**: Mark todos as completed by searching for their title
- **Search Functionality**: Search through all todos by title or content

### Advanced Viewing (NEW)
- **View Logbook**: See recently completed tasks with completion dates
- **View by Tag**: Filter tasks across all lists by specific tags
- **View Project Tasks**: See all tasks within a specific project
- **View Overdue**: Identify tasks that have passed their deadline
- **View Repeating**: List all recurring/repeating tasks

### Statistics & Review (NEW)
- **Task Counts**: Get quick counts across all Things3 lists
- **Weekly Review**: Generate comprehensive GTD-style weekly review summaries

### Task Management (NEW)
- **Quick Add**: Ultra-fast task capture to inbox
- **Cancel Todo**: Cancel/abandon tasks by title
- **Reschedule Todo**: Move tasks to new dates with natural language ("tomorrow", "next week")
- **Bulk Complete**: Complete multiple tasks at once

### Navigation (NEW)
- **Show in Things**: Open Things3 to any view, project, or tag directly

### Technical
- **Robust Error Handling**: Comprehensive validation and error recovery
- **Secure URL Encoding**: Proper handling of special characters and unicode
- **AppleScript Integration**: Safe, non-JSON string concatenation approach

## Installation

### Prerequisites
- macOS with Things3 installed
- Python 3.8+ 
- Things3 running (for real-time operations)

### Install the Server

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd mcp-things3
   ```

2. Install using pip:
   ```bash
   pip install -e .
   ```

3. The server will be available as `mcp-server-things3`

## Tools Available

### View Operations

#### `view-inbox`
View all todos in the Things3 inbox.
- **Parameters**: None
- **Returns**: List of inbox todos with due dates and scheduling info

#### `view-projects`
View all projects in Things3.
- **Parameters**: None  
- **Returns**: List of all projects with their titles

#### `view-todos`
View all todos in today's list.
- **Parameters**: None
- **Returns**: List of today's todos with metadata

### Creation Operations

#### `create-things3-project`
Creates a new project in Things3.
- **Required**: `title` (string)
- **Optional**: 
  - `notes` (string)
  - `area` (string) 
  - `when` (string) - Date/time to start
  - `deadline` (string) - Due date
  - `tags` (array of strings)

**Example**:
```json
{
  "title": "Website Redesign",
  "notes": "Complete overhaul of company website",
  "area": "Work",
  "deadline": "2024-03-15",
  "tags": ["urgent", "web-dev"]
}
```

#### `create-things3-todo`
Creates a new to-do in Things3.
- **Required**: `title` (string)
- **Optional**:
  - `notes` (string)
  - `when` (string) - Date/time to start  
  - `deadline` (string) - Due date
  - `checklist` (array of strings)
  - `tags` (array of strings)
  - `list` (string) - Project or area to assign to
  - `heading` (string) - Group under this heading

**Example**:
```json
{
  "title": "Review design mockups",
  "notes": "Check the new homepage designs",
  "list": "Website Redesign", 
  "deadline": "2024-02-20",
  "tags": ["review"],
  "checklist": ["Check mobile responsiveness", "Verify brand guidelines", "Test accessibility"]
}
```

### Management Operations

#### `complete-things3-todo`
Mark a todo as completed by searching for its title.
- **Required**: `title` (string) - Title or partial title to search for
- **Returns**: Success/failure message

**Example**:
```json
{
  "title": "Review design"
}
```

#### `search-things3-todos`
Search for todos by title or content.
- **Required**: `query` (string) - Search term
- **Returns**: List of matching todos with status and metadata

**Example**:
```json
{
  "query": "website"
}
```

### Advanced View Operations (NEW)

#### `view-logbook`
View recently completed tasks from the logbook.
- **Optional**:
  - `limit` (integer) - Maximum tasks to return (default: 50, max: 200)
  - `days` (integer) - Only tasks completed within this many days (default: 7)
- **Returns**: List of completed tasks with completion dates

**Example**:
```json
{
  "limit": 20,
  "days": 14
}
```

#### `view-by-tag`
View all tasks with a specific tag across all lists.
- **Required**: `tag` (string) - The tag name to filter by
- **Optional**: `include_completed` (boolean) - Include completed tasks (default: false)
- **Returns**: List of tasks with the specified tag

**Example**:
```json
{
  "tag": "work",
  "include_completed": false
}
```

#### `view-project-tasks`
View all tasks within a specific project.
- **Required**: `project_name` (string) - Exact name of the project
- **Returns**: Project metadata and list of all tasks in the project

**Example**:
```json
{
  "project_name": "Website Redesign"
}
```

#### `view-overdue`
View all tasks that have passed their deadline.
- **Parameters**: None
- **Returns**: List of overdue tasks with days overdue count

#### `view-repeating`
View all recurring/repeating tasks.
- **Parameters**: None
- **Returns**: List of repeating tasks (note: repeat frequency is not accessible via automation)

### Statistics Operations (NEW)

#### `task-counts`
Get quick task count statistics across all Things3 lists.
- **Parameters**: None
- **Returns**: Counts for inbox, today, upcoming, anytime, someday, logbook, and total open

#### `weekly-review`
Generate a comprehensive weekly review summary for GTD workflow.
- **Optional**:
  - `days` (integer) - Days to analyze for completion stats (default: 7)
  - `stale_days` (integer) - Consider inbox items stale after this many days (default: 7)
  - `someday_review_days` (integer) - Suggest reviewing someday items older than this (default: 30)
- **Returns**: Comprehensive report including overdue tasks, inbox staleness, completion stats, and someday items to review

**Example**:
```json
{
  "days": 7,
  "stale_days": 7,
  "someday_review_days": 30
}
```

### Quick Operations (NEW)

#### `quick-add`
Ultra-simple task creation - add a task to inbox with just a title.
- **Required**: `title` (string) - The task title
- **Returns**: Confirmation of task added to inbox

**Example**:
```json
{
  "title": "Call the dentist"
}
```

### State Management Operations (NEW)

#### `cancel-todo`
Cancel/abandon a task by its title.
- **Required**: `title` (string) - Title or partial title of task to cancel
- **Returns**: Success message or list of matches if ambiguous

**Example**:
```json
{
  "title": "Old project task"
}
```

#### `reschedule-todo`
Reschedule a task to a new date.
- **Required**:
  - `title` (string) - Title or partial title of task to reschedule
  - `when` (string) - New date: 'today', 'tomorrow', 'next week', 'next monday', 'someday', 'anytime', or 'YYYY-MM-DD'
- **Returns**: Success message or list of matches if ambiguous

**Example**:
```json
{
  "title": "Review report",
  "when": "next monday"
}
```

#### `bulk-complete`
Complete multiple tasks at once.
- **Required**: `titles` (array of strings) - List of task titles to complete (max: 20)
- **Returns**: Results for each task (success, not found, or ambiguous)

**Example**:
```json
{
  "titles": ["Call client", "Send email", "Update spreadsheet"]
}
```

### Navigation Operations (NEW)

#### `show-in-things`
Open Things3 and navigate to a specific view, project, or tag.
- **Required**: `view` (string) - One of: inbox, today, upcoming, anytime, someday, logbook, tomorrow, deadlines, repeating, all-projects, project, tag
- **Optional**:
  - `name` (string) - Required when view is 'project' or 'tag'
  - `filter_tags` (array of strings) - Filter the view by these tags
- **Returns**: Confirmation of navigation

**Examples**:
```json
{
  "view": "today"
}
```

```json
{
  "view": "project",
  "name": "Website Redesign"
}
```

```json
{
  "view": "today",
  "filter_tags": ["work", "urgent"]
}
```

## Integration with Claude

This MCP server is designed to work seamlessly with Claude AI. Once configured, you can use natural language to manage your Things3 tasks:

### Basic Operations
- "Create a project called 'Q1 Planning' with a deadline of March 31st"
- "Add a todo to review the budget with a checklist of tasks"
- "Show me all my tasks for today"
- "Mark the 'Call client' task as completed"
- "Search for all todos related to the website project"

### Advanced Operations (NEW)
- "What did I complete last week?"
- "Show me all tasks tagged with 'urgent'"
- "What tasks are overdue?"
- "Give me a weekly review summary"
- "How many tasks do I have in each list?"
- "Quick add 'Call the dentist' to my inbox"
- "Cancel the 'Old project' task"
- "Reschedule 'Review report' to next Monday"
- "Complete these tasks: 'Call client', 'Send email', 'Update docs'"
- "Open Things to show my Today view"
- "Show me the 'Website Redesign' project in Things"

## Configuration

### MCP Client Configuration

Add to your MCP client configuration (e.g., Claude Desktop config):

```json
{
  "mcpServers": {
    "things3": {
      "command": "mcp-server-things3",
      "args": []
    }
  }
}
```

### Things3 Setup

1. Ensure Things3 is installed and running
2. Grant necessary permissions when prompted for AppleScript access
3. The server will validate Things3 availability before operations

## Architecture

### Components

- **`server.py`**: Main MCP server implementation with tool definitions and handlers
- **`applescript_handler.py`**: Robust AppleScript integration with safe data parsing
- **URL Encoding**: Proper x-callback-url parameter encoding for special characters
- **Error Handling**: Comprehensive validation and graceful error recovery

### Security Features

- **Input Sanitization**: All user inputs are properly escaped for AppleScript
- **URL Encoding**: Special characters and unicode properly handled in URLs
- **Validation**: Things3 availability checked before operations
- **Error Recovery**: Graceful handling of AppleScript and system errors

## Development

### Running Tests

```bash
python test_things3.py
```

### Debugging

The server includes comprehensive logging. Set log level for debugging:

```bash
export PYTHONPATH="."
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from src.mcp_server_things3.server import main
import asyncio
asyncio.run(main())
"
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Troubleshooting

### Common Issues

**"Things3 is not available"**
- Ensure Things3 is installed and running
- Grant AppleScript permissions when prompted
- Check Things3 is not in a permission-restricted mode

**"Failed to execute AppleScript"**
- Verify macOS security settings allow AppleScript
- Ensure Things3 has necessary accessibility permissions
- Try restarting Things3

**URL encoding issues with special characters**
- The server now properly handles unicode and special characters
- If issues persist, check the logs for specific URL construction errors

### Performance Notes

- AppleScript operations may have slight delays
- Large todo lists (1000+ items) may take longer to search
- Consider using specific searches rather than broad queries for better performance

## License

MIT License - see LICENSE file for details.

## Changelog

### v0.2.0 (Enhanced)
- **12 New Tools** for comprehensive Things3 integration
- **Advanced Viewing**: view-logbook, view-by-tag, view-project-tasks, view-overdue, view-repeating
- **Statistics & GTD**: task-counts, weekly-review for GTD workflow support
- **Quick Operations**: quick-add for fast task capture
- **State Management**: cancel-todo, reschedule-todo, bulk-complete with ambiguous match handling
- **Navigation**: show-in-things to open Things3 to specific views
- Natural language date parsing (tomorrow, next week, next monday)
- Improved response formatting with icons and consistent structure

### v0.1.0
- Initial release with basic CRUD operations
- Comprehensive error handling and validation
- Secure URL encoding and AppleScript integration
- Search and completion functionality
- Robust data parsing without JSON string concatenation
