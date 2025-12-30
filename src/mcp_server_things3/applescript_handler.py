import subprocess
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import re

class AppleScriptHandler:
    """Handles AppleScript execution for Things3 data retrieval."""

    @staticmethod
    def run_script(script: str) -> str:
        """
        Executes an AppleScript and returns its output.
        """
        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                check=True,
                capture_output=True,
                text=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to execute AppleScript: {e}")

    @staticmethod
    def safe_string_for_applescript(text: str) -> str:
        """
        Safely escape a string for use in AppleScript by handling quotes and special characters.
        """
        if not text:
            return ""
        
        # Replace backslashes first to avoid double escaping
        text = text.replace("\\", "\\\\")
        # Replace quotes with escaped quotes
        text = text.replace('"', '\\"')
        # Replace newlines with \\n
        text = text.replace("\n", "\\n")
        text = text.replace("\r", "\\r")
        
        return text

    @staticmethod
    def parse_applescript_record(record_str: str) -> Dict[str, Any]:
        """
        Parse an AppleScript record string into a Python dictionary.
        More robust than string concatenation for JSON.
        """
        result = {}
        
        # Remove outer braces if present
        record_str = record_str.strip()
        if record_str.startswith('{') and record_str.endswith('}'):
            record_str = record_str[1:-1]
        
        # Split by commas but be careful about nested structures
        parts = []
        current_part = ""
        brace_count = 0
        
        for char in record_str:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
            elif char == ',' and brace_count == 0:
                parts.append(current_part.strip())
                current_part = ""
                continue
            current_part += char
        
        if current_part.strip():
            parts.append(current_part.strip())
        
        # Parse each key-value pair
        for part in parts:
            if ':' in part:
                key, value = part.split(':', 1)
                key = key.strip().strip('"\'')
                value = value.strip().strip('"\'')
                result[key] = value
        
        return result

    @staticmethod
    def get_inbox_tasks() -> List[Dict[str, Any]]:
        """
        Retrieves tasks from the Inbox using AppleScript with delimited output.
        """
        script = '''
        tell application "Things3"
            set inboxTasks to to dos of list "Inbox"
            set outputLines to {}

            repeat with t in inboxTasks
                set taskTitle to name of t

                set taskNotes to ""
                if notes of t is not missing value then
                    set taskNotes to notes of t
                end if

                set dueDate to ""
                if due date of t is not missing value then
                    set dueDate to ((due date of t) as string)
                end if

                set whenDate to ""
                if activation date of t is not missing value then
                    set whenDate to ((activation date of t) as string)
                end if

                set tagText to ""
                try
                    set tagList to tag names of t
                    if tagList is not {} then
                        set AppleScript's text item delimiters to ","
                        set tagText to tagList as string
                        set AppleScript's text item delimiters to ""
                    end if
                end try

                -- Use ||| as field delimiter, %%% as record delimiter
                set taskLine to taskTitle & "|||" & taskNotes & "|||" & dueDate & "|||" & whenDate & "|||" & tagText
                set end of outputLines to taskLine
            end repeat

            set AppleScript's text item delimiters to "%%%"
            set outputText to outputLines as string
            set AppleScript's text item delimiters to ""
            return outputText
        end tell
        '''

        try:
            result = AppleScriptHandler.run_script(script)

            if not result or result == "":
                return []

            tasks = []
            records = result.split("%%%")

            for record in records:
                if not record.strip():
                    continue
                fields = record.split("|||")
                task = {
                    "title": fields[0] if len(fields) > 0 else "",
                    "notes": fields[1] if len(fields) > 1 else "",
                    "due_date": fields[2] if len(fields) > 2 else "",
                    "when": fields[3] if len(fields) > 3 else "",
                    "tags": fields[4] if len(fields) > 4 else ""
                }
                tasks.append(task)

            return tasks

        except Exception as e:
            print(f"Error retrieving inbox tasks: {e}", file=__import__('sys').stderr)
            return []

    @staticmethod
    def get_todays_tasks() -> List[Dict[str, Any]]:
        """
        Retrieves today's tasks from Things3 using AppleScript with delimited output.
        """
        script = '''
        tell application "Things3"
            set todayTasks to to dos of list "Today"
            set outputLines to {}

            repeat with t in todayTasks
                set taskTitle to name of t

                set taskNotes to ""
                if notes of t is not missing value then
                    set taskNotes to notes of t
                end if

                set dueDate to ""
                if due date of t is not missing value then
                    set dueDate to ((due date of t) as string)
                end if

                set whenDate to ""
                if activation date of t is not missing value then
                    set whenDate to ((activation date of t) as string)
                end if

                set tagText to ""
                try
                    set tagList to tag names of t
                    if tagList is not {} then
                        set AppleScript's text item delimiters to ","
                        set tagText to tagList as string
                        set AppleScript's text item delimiters to ""
                    end if
                end try

                -- Use ||| as field delimiter, %%% as record delimiter
                set taskLine to taskTitle & "|||" & taskNotes & "|||" & dueDate & "|||" & whenDate & "|||" & tagText
                set end of outputLines to taskLine
            end repeat

            set AppleScript's text item delimiters to "%%%"
            set outputText to outputLines as string
            set AppleScript's text item delimiters to ""
            return outputText
        end tell
        '''

        try:
            result = AppleScriptHandler.run_script(script)

            if not result or result == "":
                return []

            tasks = []
            records = result.split("%%%")

            for record in records:
                if not record.strip():
                    continue
                fields = record.split("|||")
                task = {
                    "title": fields[0] if len(fields) > 0 else "",
                    "notes": fields[1] if len(fields) > 1 else "",
                    "due_date": fields[2] if len(fields) > 2 else "",
                    "when": fields[3] if len(fields) > 3 else "",
                    "tags": fields[4] if len(fields) > 4 else ""
                }
                tasks.append(task)

            return tasks

        except Exception as e:
            print(f"Error retrieving today's tasks: {e}", file=__import__('sys').stderr)
            return []

    @staticmethod
    def get_projects() -> List[Dict[str, str]]:
        """
        Retrieves all projects from Things3 using AppleScript with delimited output.
        """
        script = '''
        tell application "Things3"
            set projectList to projects
            set outputLines to {}

            repeat with p in projectList
                set projectTitle to name of p
                set projectNotes to ""
                if notes of p is not missing value then
                    set projectNotes to notes of p
                end if

                -- Use ||| as field delimiter, %%% as record delimiter
                set projectLine to projectTitle & "|||" & projectNotes
                set end of outputLines to projectLine
            end repeat

            set AppleScript's text item delimiters to "%%%"
            set outputText to outputLines as string
            set AppleScript's text item delimiters to ""
            return outputText
        end tell
        '''

        try:
            result = AppleScriptHandler.run_script(script)

            if not result or result == "":
                return []

            projects = []
            records = result.split("%%%")

            for record in records:
                if not record.strip():
                    continue
                fields = record.split("|||")
                project = {
                    "title": fields[0] if len(fields) > 0 else "",
                    "notes": fields[1] if len(fields) > 1 else ""
                }
                projects.append(project)

            return projects

        except Exception as e:
            print(f"Error retrieving projects: {e}", file=__import__('sys').stderr)
            return []

    @staticmethod
    def validate_things3_access() -> bool:
        """
        Validate that Things3 is accessible and responsive.
        """
        try:
            script = '''
            tell application "Things3"
                return name of application "Things3"
            end tell
            '''
            result = AppleScriptHandler.run_script(script)
            return "Things3" in result
        except Exception:
            return False

    @staticmethod
    def complete_todo_by_title(title_search: str) -> bool:
        """
        Mark a todo as completed by searching for its title.
        """
        script = f'''
        tell application "Things3"
            set foundTodo to missing value
            
            -- Search in Today list
            set todayTodos to to dos of list "Today"
            repeat with t in todayTodos
                if name of t contains "{AppleScriptHandler.safe_string_for_applescript(title_search)}" then
                    set foundTodo to t
                    exit repeat
                end if
            end repeat
            
            -- If not found in Today, search in Inbox
            if foundTodo is missing value then
                set inboxTodos to to dos of list "Inbox"
                repeat with t in inboxTodos
                    if name of t contains "{AppleScriptHandler.safe_string_for_applescript(title_search)}" then
                        set foundTodo to t
                        exit repeat
                    end if
                end repeat
            end if
            
            -- If not found in standard lists, search all todos
            if foundTodo is missing value then
                set allTodos to to dos
                repeat with t in allTodos
                    if name of t contains "{AppleScriptHandler.safe_string_for_applescript(title_search)}" and status of t is not completed then
                        set foundTodo to t
                        exit repeat
                    end if
                end repeat
            end if
            
            -- Complete the todo if found
            if foundTodo is not missing value then
                set status of foundTodo to completed
                return "COMPLETED:" & name of foundTodo
            else
                return "NOT_FOUND"
            end if
        end tell
        '''
        
        try:
            result = AppleScriptHandler.run_script(script)
            return result.startswith("COMPLETED:")
        except Exception:
            return False

    # ===========================================
    # T008-T012: User Story 1 - View Methods
    # ===========================================

    @staticmethod
    def get_logbook_tasks(limit: int = 50, days: int = 7) -> List[Dict[str, Any]]:
        """
        Retrieve completed tasks from the logbook.

        Args:
            limit: Maximum number of tasks to return
            days: Only return tasks completed within this many days

        Returns:
            List of completed tasks with completion dates
        """
        script = f'''
        tell application "Things3"
            set logbookTasks to to dos of list "Logbook"
            set outputLines to {{}}
            set taskCount to 0
            set maxTasks to {limit}
            set cutoffDate to (current date) - ({days} * days)

            repeat with t in logbookTasks
                if taskCount >= maxTasks then exit repeat

                set completionDate to ""
                if completion date of t is not missing value then
                    set completionDate to ((completion date of t) as string)
                    -- Check if within date range
                    if completion date of t >= cutoffDate then
                        set taskTitle to name of t

                        set taskNotes to ""
                        if notes of t is not missing value then
                            set taskNotes to notes of t
                        end if

                        set taskProject to ""
                        try
                            if project of t is not missing value then
                                set taskProject to name of project of t
                            end if
                        end try

                        set tagText to ""
                        try
                            set tagList to tag names of t
                            if tagList is not {{}} then
                                set AppleScript's text item delimiters to ","
                                set tagText to tagList as string
                                set AppleScript's text item delimiters to ""
                            end if
                        end try

                        -- Use ||| as field delimiter, %%% as record delimiter
                        set taskLine to taskTitle & "|||" & taskNotes & "|||" & completionDate & "|||" & taskProject & "|||" & tagText
                        set end of outputLines to taskLine
                        set taskCount to taskCount + 1
                    end if
                end if
            end repeat

            set AppleScript's text item delimiters to "%%%"
            set outputText to outputLines as string
            set AppleScript's text item delimiters to ""
            return outputText
        end tell
        '''

        try:
            result = AppleScriptHandler.run_script(script)

            if not result or result == "":
                return []

            tasks = []
            records = result.split("%%%")

            for record in records:
                if not record.strip():
                    continue
                fields = record.split("|||")
                task = {
                    "title": fields[0] if len(fields) > 0 else "",
                    "notes": fields[1] if len(fields) > 1 else "",
                    "completion_date": fields[2] if len(fields) > 2 else "",
                    "project": fields[3] if len(fields) > 3 else "",
                    "tags": fields[4] if len(fields) > 4 else ""
                }
                tasks.append(task)

            return tasks

        except Exception as e:
            print(f"Error retrieving logbook tasks: {e}", file=__import__('sys').stderr)
            return []

    @staticmethod
    def get_tasks_by_tag(tag_name: str, include_completed: bool = False) -> List[Dict[str, Any]]:
        """
        Retrieve all tasks with a specific tag.

        Args:
            tag_name: The tag name to filter by
            include_completed: Whether to include completed tasks

        Returns:
            List of tasks with the specified tag
        """
        status_filter = "" if include_completed else "and status of t is open"

        script = f'''
        tell application "Things3"
            set taggedTodos to {{}}
            try
                set targetTag to tag "{AppleScriptHandler.safe_string_for_applescript(tag_name)}"
                set allTaggedTodos to to dos of targetTag

                repeat with t in allTaggedTodos
                    if true {status_filter} then
                        set taskId to id of t
                        set taskTitle to name of t

                        set taskNotes to ""
                        if notes of t is not missing value then
                            set taskNotes to notes of t
                        end if

                        set dueDate to ""
                        if due date of t is not missing value then
                            set dueDate to ((due date of t) as string)
                        end if

                        set whenDate to ""
                        if activation date of t is not missing value then
                            set whenDate to ((activation date of t) as string)
                        end if

                        set taskProject to ""
                        try
                            if project of t is not missing value then
                                set taskProject to name of project of t
                            end if
                        end try

                        set taskStatus to "open"
                        if status of t is completed then
                            set taskStatus to "completed"
                        else if status of t is canceled then
                            set taskStatus to "canceled"
                        end if

                        set taskRecord to {{task_id:taskId, title:taskTitle, notes:taskNotes, due_date:dueDate, when_date:whenDate, project:taskProject, status:taskStatus}}
                        set end of taggedTodos to taskRecord
                    end if
                end repeat
            on error errMsg
                return {{}}
            end try

            return taggedTodos
        end tell
        '''

        try:
            result = AppleScriptHandler.run_script(script)

            if not result or result == "{}" or result == "":
                return []

            tasks = []
            if result.startswith('{{') and result.endswith('}}'):
                records_str = result[2:-2]
                record_strings = re.split(r'\}, \{', records_str)

                for record_str in record_strings:
                    record_str = record_str.strip()
                    if not record_str.startswith('{'):
                        record_str = '{' + record_str
                    if not record_str.endswith('}'):
                        record_str = record_str + '}'

                    task_data = AppleScriptHandler.parse_applescript_record(record_str)
                    task = {
                        "id": task_data.get("task_id", ""),
                        "title": task_data.get("title", ""),
                        "notes": task_data.get("notes", ""),
                        "due_date": task_data.get("due_date", ""),
                        "when": task_data.get("when_date", ""),
                        "project": task_data.get("project", ""),
                        "status": task_data.get("status", "open")
                    }
                    tasks.append(task)

            return tasks

        except Exception as e:
            print(f"Error retrieving tasks by tag: {e}")
            return []

    @staticmethod
    def get_project_tasks(project_name: str) -> Dict[str, Any]:
        """
        Retrieve all tasks within a specific project.

        Args:
            project_name: The name of the project

        Returns:
            Dictionary with project metadata and tasks list
        """
        script = f'''
        tell application "Things3"
            try
                set targetProject to project "{AppleScriptHandler.safe_string_for_applescript(project_name)}"
                set projectTasks to to dos of targetProject

                set projectNotes to ""
                if notes of targetProject is not missing value then
                    set projectNotes to notes of targetProject
                end if

                set projectDueDate to ""
                if due date of targetProject is not missing value then
                    set projectDueDate to ((due date of targetProject) as string)
                end if

                set resultList to {{}}

                repeat with t in projectTasks
                    set taskId to id of t
                    set taskTitle to name of t

                    set taskNotes to ""
                    if notes of t is not missing value then
                        set taskNotes to notes of t
                    end if

                    set dueDate to ""
                    if due date of t is not missing value then
                        set dueDate to ((due date of t) as string)
                    end if

                    set whenDate to ""
                    if activation date of t is not missing value then
                        set whenDate to ((activation date of t) as string)
                    end if

                    set taskStatus to "open"
                    if status of t is completed then
                        set taskStatus to "completed"
                    else if status of t is canceled then
                        set taskStatus to "canceled"
                    end if

                    set tagText to ""
                    try
                        set tagList to tag names of t
                        if tagList is not {{}} then
                            set AppleScript's text item delimiters to ","
                            set tagText to tagList as string
                            set AppleScript's text item delimiters to ""
                        end if
                    end try

                    set taskRecord to {{task_id:taskId, title:taskTitle, notes:taskNotes, due_date:dueDate, when_date:whenDate, status:taskStatus, tags:tagText}}
                    set end of resultList to taskRecord
                end repeat

                return "PROJECT_NOTES:" & projectNotes & "|PROJECT_DEADLINE:" & projectDueDate & "|TASKS:" & (resultList as string)
            on error errMsg
                return "PROJECT_NOT_FOUND"
            end try
        end tell
        '''

        try:
            result = AppleScriptHandler.run_script(script)

            if not result or result == "PROJECT_NOT_FOUND":
                return {"error": "Project not found", "project": project_name, "tasks": []}

            # Parse the custom format
            project_notes = ""
            project_deadline = ""
            tasks = []

            if "PROJECT_NOTES:" in result:
                parts = result.split("|")
                for part in parts:
                    if part.startswith("PROJECT_NOTES:"):
                        project_notes = part[14:]
                    elif part.startswith("PROJECT_DEADLINE:"):
                        project_deadline = part[17:]
                    elif part.startswith("TASKS:"):
                        tasks_str = part[6:]
                        if tasks_str.startswith('{{') and tasks_str.endswith('}}'):
                            records_str = tasks_str[2:-2]
                            record_strings = re.split(r'\}, \{', records_str)

                            for record_str in record_strings:
                                record_str = record_str.strip()
                                if not record_str.startswith('{'):
                                    record_str = '{' + record_str
                                if not record_str.endswith('}'):
                                    record_str = record_str + '}'

                                task_data = AppleScriptHandler.parse_applescript_record(record_str)
                                task = {
                                    "id": task_data.get("task_id", ""),
                                    "title": task_data.get("title", ""),
                                    "notes": task_data.get("notes", ""),
                                    "due_date": task_data.get("due_date", ""),
                                    "when": task_data.get("when_date", ""),
                                    "status": task_data.get("status", "open"),
                                    "tags": task_data.get("tags", "")
                                }
                                tasks.append(task)

            return {
                "project": project_name,
                "notes": project_notes,
                "deadline": project_deadline,
                "tasks": tasks,
                "count": len(tasks)
            }

        except Exception as e:
            print(f"Error retrieving project tasks: {e}")
            return {"error": str(e), "project": project_name, "tasks": []}

    @staticmethod
    def get_overdue_tasks() -> List[Dict[str, Any]]:
        """
        Retrieve all overdue tasks (due date in the past).

        Returns:
            List of overdue tasks with days_overdue field
        """
        script = '''
        tell application "Things3"
            set today to current date
            set overdueTasks to {}
            set allTodos to to dos whose status is open

            repeat with t in allTodos
                if due date of t is not missing value then
                    if due date of t < today then
                        set taskId to id of t
                        set taskTitle to name of t
                        set dueDate to ((due date of t) as string)

                        -- Calculate days overdue
                        set daysOverdue to ((today - (due date of t)) / days) as integer

                        set taskNotes to ""
                        if notes of t is not missing value then
                            set taskNotes to notes of t
                        end if

                        set taskProject to ""
                        try
                            if project of t is not missing value then
                                set taskProject to name of project of t
                            end if
                        end try

                        set tagText to ""
                        try
                            set tagList to tag names of t
                            if tagList is not {} then
                                set AppleScript's text item delimiters to ","
                                set tagText to tagList as string
                                set AppleScript's text item delimiters to ""
                            end if
                        end try

                        set taskRecord to {task_id:taskId, title:taskTitle, due_date:dueDate, days_overdue:daysOverdue, notes:taskNotes, project:taskProject, tags:tagText}
                        set end of overdueTasks to taskRecord
                    end if
                end if
            end repeat

            return overdueTasks
        end tell
        '''

        try:
            result = AppleScriptHandler.run_script(script)

            if not result or result == "{}" or result == "":
                return []

            tasks = []
            if result.startswith('{{') and result.endswith('}}'):
                records_str = result[2:-2]
                record_strings = re.split(r'\}, \{', records_str)

                for record_str in record_strings:
                    record_str = record_str.strip()
                    if not record_str.startswith('{'):
                        record_str = '{' + record_str
                    if not record_str.endswith('}'):
                        record_str = record_str + '}'

                    task_data = AppleScriptHandler.parse_applescript_record(record_str)
                    task = {
                        "id": task_data.get("task_id", ""),
                        "title": task_data.get("title", ""),
                        "due_date": task_data.get("due_date", ""),
                        "days_overdue": int(task_data.get("days_overdue", 0)) if task_data.get("days_overdue") else 0,
                        "notes": task_data.get("notes", ""),
                        "project": task_data.get("project", ""),
                        "tags": task_data.get("tags", "")
                    }
                    tasks.append(task)

            # Sort by days overdue (most overdue first)
            tasks.sort(key=lambda x: x.get("days_overdue", 0), reverse=True)

            return tasks

        except Exception as e:
            print(f"Error retrieving overdue tasks: {e}")
            return []

    # ===========================================
    # T034-T036: User Story 4 - State Management Methods
    # ===========================================

    @staticmethod
    def cancel_todo_by_title(title_search: str) -> Dict[str, Any]:
        """
        Cancel a task by title search.

        Args:
            title_search: Title or partial title to search for

        Returns:
            Dictionary with result status and details
        """
        script = f'''
        tell application "Things3"
            set searchQuery to "{AppleScriptHandler.safe_string_for_applescript(title_search)}"
            set foundTodos to {{}}

            repeat with t in to dos
                if name of t contains searchQuery and status of t is open then
                    set taskId to id of t
                    set taskTitle to name of t
                    set taskProject to ""
                    try
                        if project of t is not missing value then
                            set taskProject to name of project of t
                        end if
                    end try
                    set taskRecord to {{task_id:taskId, title:taskTitle, project:taskProject}}
                    set end of foundTodos to taskRecord
                end if
            end repeat

            if (count of foundTodos) = 0 then
                return "NOT_FOUND"
            else if (count of foundTodos) = 1 then
                set targetId to task_id of item 1 of foundTodos
                set targetTitle to title of item 1 of foundTodos
                repeat with t in to dos
                    if id of t = targetId then
                        set status of t to canceled
                        return "CANCELED:" & targetTitle
                    end if
                end repeat
            else
                return "AMBIGUOUS:" & (count of foundTodos) & "|" & (foundTodos as string)
            end if
        end tell
        '''

        try:
            result = AppleScriptHandler.run_script(script)

            if result.startswith("CANCELED:"):
                return {
                    "status": "success",
                    "action": "canceled",
                    "title": result[9:]
                }
            elif result == "NOT_FOUND":
                return {
                    "status": "not_found",
                    "message": f"No open task found matching '{title_search}'"
                }
            elif result.startswith("AMBIGUOUS:"):
                # Parse the ambiguous result
                parts = result.split("|", 1)
                count = int(parts[0].replace("AMBIGUOUS:", ""))
                matches = AppleScriptHandler.find_matching_tasks(title_search)
                return {
                    "status": "ambiguous",
                    "count": count,
                    "matches": matches,
                    "message": f"Multiple tasks ({count}) match '{title_search}'. Please be more specific."
                }
            else:
                return {"status": "error", "message": "Unexpected response"}

        except Exception as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def reschedule_todo_by_title(title_search: str, new_when: str) -> Dict[str, Any]:
        """
        Reschedule a task to a new date by title search.

        Args:
            title_search: Title or partial title to search for
            new_when: New date (supports natural language like 'tomorrow', 'next week')

        Returns:
            Dictionary with result status and details
        """
        # Parse the date first
        parsed_date = AppleScriptHandler.parse_natural_date(new_when)
        if not parsed_date:
            return {
                "status": "error",
                "message": f"Could not parse date: '{new_when}'. Try formats like 'tomorrow', 'next monday', 'next week', or 'YYYY-MM-DD'"
            }

        when_value = parsed_date

        # Determine if we need to use 'schedule' command (for dates) or 'move' (for special lists)
        # Special lists that use 'move to list' command
        special_lists = {
            "someday": "Someday",
            "anytime": "Anytime",
        }

        # Check if this is a special list (use move) or a date (use schedule)
        use_move_command = when_value.lower() in special_lists

        if use_move_command:
            target_list = special_lists[when_value.lower()]
            schedule_part = f'move t to list "{target_list}"'
        elif when_value.lower() == "today":
            # For today, move to Today list
            schedule_part = 'move t to list "Today"'
        elif when_value.lower() == "evening":
            # For evening, move to Today list (Things handles evening internally)
            schedule_part = 'move t to list "Today"'
        elif when_value.lower() == "tomorrow":
            # Use schedule command for tomorrow
            schedule_part = 'schedule t for (current date) + 1 * days'
        elif when_value.lower() == "next week":
            # Use schedule command for next week (7 days)
            schedule_part = 'schedule t for (current date) + 7 * days'
        else:
            # For specific dates (YYYY-MM-DD), calculate days from now and use schedule
            try:
                target_date = datetime.strptime(when_value, "%Y-%m-%d").date()
                today = datetime.now().date()
                days_diff = (target_date - today).days
                if days_diff < 0:
                    return {
                        "status": "error",
                        "message": f"Cannot schedule to a past date: {when_value}"
                    }
                elif days_diff == 0:
                    schedule_part = 'move t to list "Today"'
                else:
                    schedule_part = f'schedule t for (current date) + {days_diff} * days'
            except ValueError:
                return {
                    "status": "error",
                    "message": f"Invalid date format: {when_value}"
                }

        script = f'''
        tell application "Things3"
            set searchQuery to "{AppleScriptHandler.safe_string_for_applescript(title_search)}"
            set foundTodos to {{}}

            repeat with t in to dos
                if name of t contains searchQuery and status of t is open then
                    set taskId to id of t
                    set taskTitle to name of t
                    set taskProject to ""
                    try
                        if project of t is not missing value then
                            set taskProject to name of project of t
                        end if
                    end try
                    set taskRecord to {{task_id:taskId, title:taskTitle, project:taskProject}}
                    set end of foundTodos to taskRecord
                end if
            end repeat

            if (count of foundTodos) = 0 then
                return "NOT_FOUND"
            else if (count of foundTodos) = 1 then
                set targetId to task_id of item 1 of foundTodos
                set targetTitle to title of item 1 of foundTodos
                repeat with t in to dos
                    if id of t = targetId then
                        -- Reschedule the task
                        {schedule_part}
                        return "RESCHEDULED:" & targetTitle & "|{when_value}"
                    end if
                end repeat
            else
                return "AMBIGUOUS:" & (count of foundTodos)
            end if
        end tell
        '''

        try:
            result = AppleScriptHandler.run_script(script)

            if result.startswith("RESCHEDULED:"):
                parts = result[12:].split("|")
                title = parts[0] if parts else title_search
                scheduled = parts[1] if len(parts) > 1 else when_value
                return {
                    "status": "success",
                    "action": "rescheduled",
                    "title": title,
                    "scheduled_to": scheduled
                }
            elif result == "NOT_FOUND":
                return {
                    "status": "not_found",
                    "message": f"No open task found matching '{title_search}'"
                }
            elif result.startswith("AMBIGUOUS:"):
                count = int(result.replace("AMBIGUOUS:", ""))
                matches = AppleScriptHandler.find_matching_tasks(title_search)
                return {
                    "status": "ambiguous",
                    "count": count,
                    "matches": matches,
                    "message": f"Multiple tasks ({count}) match '{title_search}'. Please be more specific."
                }
            else:
                return {"status": "error", "message": "Unexpected response"}

        except Exception as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def bulk_complete_todos(titles: List[str]) -> Dict[str, Any]:
        """
        Complete multiple tasks by their titles.

        Args:
            titles: List of task titles to complete

        Returns:
            Dictionary with results for each task
        """
        results = []
        succeeded = 0
        failed = 0

        for title in titles:
            try:
                success = AppleScriptHandler.complete_todo_by_title(title)
                if success:
                    results.append({"title": title, "status": "success"})
                    succeeded += 1
                else:
                    # Try to find if there are multiple matches
                    matches = AppleScriptHandler.find_matching_tasks(title)
                    if len(matches) > 1:
                        results.append({
                            "title": title,
                            "status": "ambiguous",
                            "matches": len(matches),
                            "error": f"Multiple tasks match '{title}'"
                        })
                    else:
                        results.append({
                            "title": title,
                            "status": "not_found",
                            "error": f"No open task found matching '{title}'"
                        })
                    failed += 1
            except Exception as e:
                results.append({"title": title, "status": "error", "error": str(e)})
                failed += 1

        return {
            "operation": "bulk_complete",
            "requested": len(titles),
            "succeeded": succeeded,
            "failed": failed,
            "results": results
        }

    # ===========================================
    # T023-T026: User Story 2 - Statistics Methods
    # ===========================================

    @staticmethod
    def get_task_counts() -> Dict[str, int]:
        """
        Get task counts for all standard lists.

        Returns:
            Dictionary with counts for each list
        """
        script = '''
        tell application "Things3"
            set inboxCount to count of to dos of list "Inbox"
            set todayCount to count of to dos of list "Today"
            set upcomingCount to count of to dos of list "Upcoming"
            set anytimeCount to count of to dos of list "Anytime"
            set somedayCount to count of to dos of list "Someday"
            set logbookCount to count of to dos of list "Logbook"

            return "inbox:" & inboxCount & ",today:" & todayCount & ",upcoming:" & upcomingCount & ",anytime:" & anytimeCount & ",someday:" & somedayCount & ",logbook:" & logbookCount
        end tell
        '''

        try:
            result = AppleScriptHandler.run_script(script)

            counts = {}
            if result:
                pairs = result.split(",")
                for pair in pairs:
                    if ":" in pair:
                        key, value = pair.split(":")
                        counts[key.strip()] = int(value.strip())

            # Calculate total open tasks
            counts["total_open"] = (
                counts.get("inbox", 0) +
                counts.get("today", 0) +
                counts.get("upcoming", 0) +
                counts.get("anytime", 0) +
                counts.get("someday", 0)
            )

            return counts

        except Exception as e:
            print(f"Error getting task counts: {e}")
            return {}

    @staticmethod
    def get_inbox_with_ages() -> List[Dict[str, Any]]:
        """
        Get inbox tasks with their creation dates and calculated ages.

        Returns:
            List of inbox tasks with age_days field
        """
        script = '''
        tell application "Things3"
            set inboxTasks to to dos of list "Inbox"
            set resultList to {}
            set today to current date

            repeat with t in inboxTasks
                set taskTitle to name of t
                set taskId to id of t

                set creationDate to ""
                set ageDays to 0
                if creation date of t is not missing value then
                    set creationDate to ((creation date of t) as string)
                    set ageDays to ((today - (creation date of t)) / days) as integer
                end if

                set tagText to ""
                try
                    set tagList to tag names of t
                    if tagList is not {} then
                        set AppleScript's text item delimiters to ","
                        set tagText to tagList as string
                        set AppleScript's text item delimiters to ""
                    end if
                end try

                set taskRecord to {task_id:taskId, title:taskTitle, creation_date:creationDate, age_days:ageDays, tags:tagText}
                set end of resultList to taskRecord
            end repeat

            return resultList
        end tell
        '''

        try:
            result = AppleScriptHandler.run_script(script)

            if not result or result == "{}" or result == "":
                return []

            tasks = []
            if result.startswith('{{') and result.endswith('}}'):
                records_str = result[2:-2]
                record_strings = re.split(r'\}, \{', records_str)

                for record_str in record_strings:
                    record_str = record_str.strip()
                    if not record_str.startswith('{'):
                        record_str = '{' + record_str
                    if not record_str.endswith('}'):
                        record_str = record_str + '}'

                    task_data = AppleScriptHandler.parse_applescript_record(record_str)
                    task = {
                        "id": task_data.get("task_id", ""),
                        "title": task_data.get("title", ""),
                        "creation_date": task_data.get("creation_date", ""),
                        "age_days": int(task_data.get("age_days", 0)) if task_data.get("age_days") else 0,
                        "tags": task_data.get("tags", "")
                    }
                    tasks.append(task)

            # Sort by age (oldest first)
            tasks.sort(key=lambda x: x.get("age_days", 0), reverse=True)

            return tasks

        except Exception as e:
            print(f"Error getting inbox with ages: {e}")
            return []

    @staticmethod
    def get_completion_stats(days: int = 7) -> Dict[str, Any]:
        """
        Get completion statistics for a given period.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with completion statistics
        """
        script = f'''
        tell application "Things3"
            set today to current date
            set cutoffDate to today - ({days} * days)
            set todayStart to today - (time of today)

            set completedThisWeek to 0
            set completedToday to 0
            set logbookTasks to to dos of list "Logbook"

            repeat with t in logbookTasks
                if completion date of t is not missing value then
                    if completion date of t >= cutoffDate then
                        set completedThisWeek to completedThisWeek + 1
                        if completion date of t >= todayStart then
                            set completedToday to completedToday + 1
                        end if
                    end if
                end if
            end repeat

            return "completed_period:" & completedThisWeek & ",completed_today:" & completedToday
        end tell
        '''

        try:
            result = AppleScriptHandler.run_script(script)

            stats = {"completed_period": 0, "completed_today": 0, "period_days": days}
            if result:
                pairs = result.split(",")
                for pair in pairs:
                    if ":" in pair:
                        key, value = pair.split(":")
                        stats[key.strip()] = int(value.strip())

            return stats

        except Exception as e:
            print(f"Error getting completion stats: {e}")
            return {"completed_period": 0, "completed_today": 0, "period_days": days}

    @staticmethod
    def get_someday_with_ages() -> List[Dict[str, Any]]:
        """
        Get someday tasks with their ages for review purposes.

        Returns:
            List of someday tasks with age_days field
        """
        script = '''
        tell application "Things3"
            set somedayTasks to to dos of list "Someday"
            set resultList to {}
            set today to current date

            repeat with t in somedayTasks
                set taskTitle to name of t
                set taskId to id of t

                set creationDate to ""
                set ageDays to 0
                if creation date of t is not missing value then
                    set creationDate to ((creation date of t) as string)
                    set ageDays to ((today - (creation date of t)) / days) as integer
                end if

                set modificationDate to ""
                set daysSinceModified to 0
                if modification date of t is not missing value then
                    set modificationDate to ((modification date of t) as string)
                    set daysSinceModified to ((today - (modification date of t)) / days) as integer
                end if

                set taskProject to ""
                try
                    if project of t is not missing value then
                        set taskProject to name of project of t
                    end if
                end try

                set tagText to ""
                try
                    set tagList to tag names of t
                    if tagList is not {} then
                        set AppleScript's text item delimiters to ","
                        set tagText to tagList as string
                        set AppleScript's text item delimiters to ""
                    end if
                end try

                set taskRecord to {task_id:taskId, title:taskTitle, creation_date:creationDate, age_days:ageDays, modification_date:modificationDate, days_since_modified:daysSinceModified, project:taskProject, tags:tagText}
                set end of resultList to taskRecord
            end repeat

            return resultList
        end tell
        '''

        try:
            result = AppleScriptHandler.run_script(script)

            if not result or result == "{}" or result == "":
                return []

            tasks = []
            if result.startswith('{{') and result.endswith('}}'):
                records_str = result[2:-2]
                record_strings = re.split(r'\}, \{', records_str)

                for record_str in record_strings:
                    record_str = record_str.strip()
                    if not record_str.startswith('{'):
                        record_str = '{' + record_str
                    if not record_str.endswith('}'):
                        record_str = record_str + '}'

                    task_data = AppleScriptHandler.parse_applescript_record(record_str)
                    task = {
                        "id": task_data.get("task_id", ""),
                        "title": task_data.get("title", ""),
                        "creation_date": task_data.get("creation_date", ""),
                        "age_days": int(task_data.get("age_days", 0)) if task_data.get("age_days") else 0,
                        "days_since_modified": int(task_data.get("days_since_modified", 0)) if task_data.get("days_since_modified") else 0,
                        "project": task_data.get("project", ""),
                        "tags": task_data.get("tags", "")
                    }
                    tasks.append(task)

            # Sort by age (oldest first)
            tasks.sort(key=lambda x: x.get("age_days", 0), reverse=True)

            return tasks

        except Exception as e:
            print(f"Error getting someday with ages: {e}")
            return []

    # ===========================================
    # T004: Shared Response Formatting Helpers
    # ===========================================

    @staticmethod
    def format_task_list(tasks: List[Dict[str, Any]], include_metadata: bool = True) -> str:
        """
        Format a list of tasks into a human-readable string.

        Args:
            tasks: List of task dictionaries
            include_metadata: Whether to include due date, tags, etc.

        Returns:
            Formatted string representation of tasks
        """
        if not tasks:
            return "No tasks found."

        lines = []
        for task in tasks:
            title = task.get("title", "Untitled")
            line = f"• {title}"

            if include_metadata:
                details = []
                if task.get("due_date"):
                    details.append(f"Due: {task['due_date']}")
                if task.get("project"):
                    details.append(f"Project: {task['project']}")
                if task.get("tags"):
                    tags = task["tags"] if isinstance(task["tags"], str) else ", ".join(task["tags"])
                    if tags:
                        details.append(f"Tags: {tags}")
                if task.get("days_overdue"):
                    details.append(f"{task['days_overdue']} days overdue")
                if task.get("completion_date"):
                    details.append(f"Completed: {task['completion_date']}")

                if details:
                    line += f" ({'; '.join(details)})"

            lines.append(line)

        return "\n".join(lines)

    @staticmethod
    def format_task_count(counts: Dict[str, int]) -> str:
        """
        Format task count statistics into a human-readable string.

        Args:
            counts: Dictionary of list names to counts

        Returns:
            Formatted string representation of counts
        """
        lines = ["Task Counts:"]
        for list_name, count in counts.items():
            # Convert snake_case to Title Case
            display_name = list_name.replace("_", " ").title()
            lines.append(f"  {display_name}: {count}")
        return "\n".join(lines)

    # ===========================================
    # T005: Date Parsing Utility
    # ===========================================

    @staticmethod
    def parse_natural_date(date_string: str) -> Optional[str]:
        """
        Parse natural language dates into YYYY-MM-DD format.

        Supported formats:
        - today, tomorrow, evening
        - next week, next monday, next tuesday, etc.
        - someday, anytime (returns special keywords)
        - YYYY-MM-DD (passed through)

        Args:
            date_string: Natural language date or ISO date string

        Returns:
            Date string in YYYY-MM-DD format or special keyword, None if unparseable
        """
        if not date_string:
            return None

        date_str = date_string.lower().strip()
        today = datetime.now().date()

        # Special keywords that Things 3 understands directly
        special_keywords = ["today", "tomorrow", "evening", "anytime", "someday"]
        if date_str in special_keywords:
            return date_str

        # Already in YYYY-MM-DD format
        if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            return date_str

        # Calculate relative dates
        weekdays = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }

        # "next week" = 7 days from now
        if date_str == "next week":
            target = today + timedelta(days=7)
            return target.strftime("%Y-%m-%d")

        # "next [weekday]" e.g., "next monday"
        if date_str.startswith("next "):
            weekday_name = date_str[5:].strip()
            if weekday_name in weekdays:
                target_weekday = weekdays[weekday_name]
                current_weekday = today.weekday()
                days_ahead = target_weekday - current_weekday
                if days_ahead <= 0:  # Target day already passed this week
                    days_ahead += 7
                target = today + timedelta(days=days_ahead)
                return target.strftime("%Y-%m-%d")

        # "in X days"
        match = re.match(r"in (\d+) days?", date_str)
        if match:
            days = int(match.group(1))
            target = today + timedelta(days=days)
            return target.strftime("%Y-%m-%d")

        return None

    # ===========================================
    # T006 & T007: Task Search Methods
    # ===========================================

    @staticmethod
    def get_task_by_title_search(title_search: str) -> Optional[Dict[str, Any]]:
        """
        Find a single task by title search, returning the task with its ID.
        Returns None if not found, or if multiple matches found.

        Args:
            title_search: Title or partial title to search for

        Returns:
            Task dictionary with 'id' field if exactly one match, None otherwise
        """
        matches = AppleScriptHandler.find_matching_tasks(title_search)

        if len(matches) == 1:
            return matches[0]
        return None

    @staticmethod
    def find_matching_tasks(title_search: str, include_completed: bool = False) -> List[Dict[str, Any]]:
        """
        Find all tasks matching a title search query.

        Args:
            title_search: Title or partial title to search for
            include_completed: Whether to include completed tasks

        Returns:
            List of matching tasks with id, title, project, and due_date
        """
        status_filter = "" if include_completed else "and status of t is not completed"

        script = f'''
        tell application "Things3"
            set searchQuery to "{AppleScriptHandler.safe_string_for_applescript(title_search)}"
            set foundTodos to {{}}
            set allTodos to to dos

            repeat with t in allTodos
                if name of t contains searchQuery {status_filter} then
                    set taskId to id of t
                    set taskTitle to name of t

                    set taskProject to ""
                    try
                        if project of t is not missing value then
                            set taskProject to name of project of t
                        end if
                    end try

                    set dueDate to ""
                    if due date of t is not missing value then
                        set dueDate to ((due date of t) as string)
                    end if

                    set taskRecord to {{task_id:taskId, title:taskTitle, project:taskProject, due_date:dueDate}}
                    set end of foundTodos to taskRecord
                end if
            end repeat

            return foundTodos
        end tell
        '''

        try:
            result = AppleScriptHandler.run_script(script)

            if not result or result == "{}" or result == "":
                return []

            tasks = []

            # Handle AppleScript list format
            if result.startswith('{{') and result.endswith('}}'):
                records_str = result[2:-2]
                record_strings = re.split(r'\}, \{', records_str)

                for record_str in record_strings:
                    record_str = record_str.strip()
                    if not record_str.startswith('{'):
                        record_str = '{' + record_str
                    if not record_str.endswith('}'):
                        record_str = record_str + '}'

                    task_data = AppleScriptHandler.parse_applescript_record(record_str)

                    task = {
                        "id": task_data.get("task_id", ""),
                        "title": task_data.get("title", ""),
                        "project": task_data.get("project", ""),
                        "due_date": task_data.get("due_date", "")
                    }
                    tasks.append(task)

            return tasks

        except Exception as e:
            print(f"Error finding matching tasks: {e}")
            return []

    @staticmethod
    def search_todos(query: str) -> List[Dict[str, Any]]:
        """
        Search for todos by title or content.
        """
        script = f'''
        tell application "Things3"
            set searchQuery to "{AppleScriptHandler.safe_string_for_applescript(query)}"
            set outputLines to {{}}
            set allTodos to to dos

            repeat with t in allTodos
                set taskTitle to name of t
                set taskNotes to ""
                if notes of t is not missing value then
                    set taskNotes to notes of t
                end if

                -- Check if query matches title or notes
                if taskTitle contains searchQuery or taskNotes contains searchQuery then
                    set taskStatus to "incomplete"
                    if status of t is completed then
                        set taskStatus to "completed"
                    end if

                    set dueDate to ""
                    if due date of t is not missing value then
                        set dueDate to ((due date of t) as string)
                    end if

                    set whenDate to ""
                    if activation date of t is not missing value then
                        set whenDate to ((activation date of t) as string)
                    end if

                    set tagText to ""
                    try
                        set tagList to tag names of t
                        if tagList is not {{}} then
                            set AppleScript's text item delimiters to ","
                            set tagText to tagList as string
                            set AppleScript's text item delimiters to ""
                        end if
                    end try

                    -- Use ||| as field delimiter, %%% as record delimiter
                    set taskLine to taskTitle & "|||" & taskNotes & "|||" & taskStatus & "|||" & dueDate & "|||" & whenDate & "|||" & tagText
                    set end of outputLines to taskLine
                end if
            end repeat

            set AppleScript's text item delimiters to "%%%"
            set outputText to outputLines as string
            set AppleScript's text item delimiters to ""
            return outputText
        end tell
        '''

        try:
            result = AppleScriptHandler.run_script(script)

            if not result or result == "":
                return []

            todos = []
            records = result.split("%%%")

            for record in records:
                if not record.strip():
                    continue
                fields = record.split("|||")
                todo = {
                    "title": fields[0] if len(fields) > 0 else "",
                    "notes": fields[1] if len(fields) > 1 else "",
                    "status": fields[2] if len(fields) > 2 else "unknown",
                    "due_date": fields[3] if len(fields) > 3 else "",
                    "when": fields[4] if len(fields) > 4 else "",
                    "tags": fields[5] if len(fields) > 5 else ""
                }
                todos.append(todo)

            return todos

        except Exception as e:
            print(f"Error searching todos: {e}", file=__import__('sys').stderr)
            return []
