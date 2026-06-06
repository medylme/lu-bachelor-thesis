#pragma once

#include <atomic>
#include <cstddef>
#include <cstdlib>
#include <new>

namespace mem_track
{

namespace detail
{
    inline std::atomic<std::size_t> current{0};
    inline std::atomic<std::size_t> peak{0};
} // namespace detail

/// Reset both current-usage and peak counters to zero.
inline void reset()
{
    detail::current.store(0, std::memory_order_relaxed);
    detail::peak.store(0, std::memory_order_relaxed);
}

/// Returns the highest observed concurrent heap usage since the last reset().
inline std::size_t peak_bytes()
{
    return detail::peak.load(std::memory_order_relaxed);
}

} // namespace mem_track

void* operator new(std::size_t n)
{
    void* ptr = std::malloc(n);
    if (!ptr) throw std::bad_alloc{};
    auto c = mem_track::detail::current.fetch_add(n, std::memory_order_relaxed) + n;
    auto p = mem_track::detail::peak.load(std::memory_order_relaxed);
    while (c > p &&
           !mem_track::detail::peak.compare_exchange_weak(
               p, c, std::memory_order_relaxed, std::memory_order_relaxed))
    {}
    return ptr;
}

void* operator new[](std::size_t n)
{
    return ::operator new(n);
}

void operator delete(void* ptr, std::size_t n) noexcept
{
    mem_track::detail::current.fetch_sub(n, std::memory_order_relaxed);
    std::free(ptr);
}

void operator delete[](void* ptr, std::size_t n) noexcept
{
    ::operator delete(ptr, n);
}

// Sized-delete fallback for compilers that don't provide size (C++14 compat).
void operator delete(void* ptr) noexcept
{
    std::free(ptr);
}

void operator delete[](void* ptr) noexcept
{
    std::free(ptr);
}
