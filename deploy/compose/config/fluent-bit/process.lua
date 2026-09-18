function process_record(tag, timestamp, record)
    if record == nil then
        return 0
    end

    -- Prefer existing service field (set by Python JSON loggers)
    if record["service"] == nil or record["service"] == "" then
        -- Fall back to Docker attrs tag
        if record["attrs"] and record["attrs"]["tag"] and record["attrs"]["tag"] ~= "" then
            record["service"] = record["attrs"]["tag"]
        else
            record["service"] = "unknown"
        end
    end

    -- If attrs exists, remove it (no longer needed)
    if record["attrs"] then
        record["attrs"] = nil
    end

    -- Handle raw log field (non-JSON that wasn't parsed)
    local log = record["log"]
    if log and type(log) == "string" then
        local parsed = parse_kong_access(log) or parse_postgresql(log) or parse_redis(log)
        if parsed then
            for k, v in pairs(parsed) do
                record[k] = v
            end
        else
            record["message"] = log
        end
        record["log"] = nil
    end

    return 1, timestamp, record
end

local function trim(s)
    return s:match("^%s*(.-)%s*$")
end

function parse_kong_access(log)
    local pattern = '^(%S+)%s+%-%s+%[([^%]]+)%]%s+"(%S+)%s+(%S+)%s+([^"]+)"%s+(%d+)%s+(%d+)%s+"([^"]*)"%s+"([^"]*)"%s*$'
    local s, e, remote_addr, timestamp, method, path, protocol, status, body_bytes, referer, ua = log:find(pattern)
    if s then
        return {remote_addr=remote_addr, timestamp=timestamp, method=method, path=path, protocol=protocol,
                status=tonumber(status), body_bytes=tonumber(body_bytes), referer=referer, user_agent=ua}
    end
    return nil
end

function parse_postgresql(log)
    local pattern = '^(%d%d%d%d%-%d%d%-%d%d%s+%d%d:%d%d:%d%d%.%d%d%d%s+%a+%s+)%[((%d+))%]:%s+(%a+):%s+(.*)$'
    local s, e, timestamp, pid, level, message = log:find(pattern)
    if s then
        return {timestamp=trim(timestamp), pid=tonumber(pid), level=level, message=message}
    end
    return nil
end

function parse_redis(log)
    local pattern = '^(%d+):(%w)%s+(%d+%s+%a+%s+%d%d%d%d%s+%d%d:%d%d:%d%d%.%d%d%d)%s+([%w%-%.%*%=])%s+(.*)$'
    local s, e, pid, role, timestamp, level_char, message = log:find(pattern)
    if s then
        local level_map = {["-"]="DEBUG", ["."]="VERBOSE", ["*"]="INFO", ["="]="WARNING", ["#"]="ERROR"}
        return {pid=tonumber(pid), role=role, timestamp=timestamp, level=level_map[level_char] or level_char, message=message}
    end
    return nil
end
