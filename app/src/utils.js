export function timestampToDate(timestamp) {
    // Javascript requires milliseconds
    const unix_timestamp = timestamp * 1000
    return new Date(unix_timestamp);
}

export function timestampToYear(timestamp) {
    const date = timestampToDate(timestamp)
    return date.getFullYear()
}

export function timestampToMonthYear(timestamp) {
    const date = timestampToDate(timestamp)
    return {
        month: date.toLocaleString('default', { month: 'long' }),
        year: date.getFullYear()
    }
}

export function timestampToDateString(timestamp) {
    const date = timestampToDate(timestamp)
    const month = date.toLocaleString('default', { month: 'long' });
    const year = date.getFullYear();
    const day = date.getDate();
    const ordinal = getOrdinalNum(day);
    return ordinal + " " + month + ' ' + year
}

function getOrdinalNum(n) {
    return n + (n > 0 ? ['th', 'st', 'nd', 'rd'][(n > 3 && n < 21) || n % 10 > 3 ? 0 : n % 10] : '');
}