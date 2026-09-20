function starter(fnName, argsPy, argsCpp, argsJava, retPy, retCpp, retJava) {
  return {
    python: `from typing import List, Optional

class Solution:
    def ${fnName}(self${argsPy}):
        # Write your solution
        pass
`,
    cpp: `#include <bits/stdc++.h>
using namespace std;

class Solution {
public:
    ${retCpp} ${fnName}(${argsCpp}) {
        
    }
};
`,
    java: `import java.util.*;

class Solution {
    public ${retJava} ${fnName}(${argsJava}) {
        
    }
}
`,
  };
}

export const MOCK_PROBLEMS = [
  {
    id: "two-sum",
    slug: "two-sum",
    title: "Two Sum",
    difficulty: "Easy",
    tags: ["Array", "Hash Table"],
    published: true,
    languages: ["python", "cpp", "java"],
    description:
      "Given an array of integers nums and an integer target, return the indices of the two numbers such that they add up to target.\n\nYou may assume that each input has exactly one solution, and you may not use the same element twice. Return the answer in any order.",
    inputFormat: "nums: list of integers\ntarget: integer",
    outputFormat: "Two indices as a list of integers.",
    examples: [
      {
        input: "nums = [2,7,11,15], target = 9",
        output: "[0,1]",
        explanation: "Because nums[0] + nums[1] == 9.",
      },
      {
        input: "nums = [3,2,4], target = 6",
        output: "[1,2]",
      },
    ],
    constraints: [
      "2 <= nums.length <= 10^4",
      "-10^9 <= nums[i] <= 10^9",
      "-10^9 <= target <= 10^9",
      "Exactly one valid answer exists.",
    ],
    starter: starter(
      "twoSum",
      ", nums: List[int], target: int",
      "vector<int>& nums, int target",
      "int[] nums, int target",
      "List[int]",
      "vector<int>",
      "int[]"
    ),
    tests: [
      { input: "[2,7,11,15]\n9", output: "[0,1]", sample: true },
      { input: "[3,2,4]\n6", output: "[1,2]", sample: true },
      { input: "[3,3]\n6", output: "[0,1]", sample: false },
    ],
  },
  {
    id: "reverse-string",
    slug: "reverse-string",
    title: "Reverse String",
    difficulty: "Easy",
    tags: ["Two Pointers", "String"],
    published: true,
    languages: ["python", "cpp", "java"],
    description:
      "Write a function that reverses a string. The input is given as an array of characters s. You must do this by modifying the input array in-place with O(1) extra memory.",
    inputFormat: "s: array of characters",
    outputFormat: "The array s after reversing in place.",
    examples: [
      { input: 's = ["h","e","l","l","o"]', output: '["o","l","l","e","h"]' },
      { input: 's = ["H","a","n","n","a","h"]', output: '["h","a","n","n","a","H"]' },
    ],
    constraints: ["1 <= s.length <= 10^5", "s[i] is a printable ascii character."],
    starter: starter(
      "reverseString",
      ", s: List[str]",
      "vector<char>& s",
      "char[] s",
      "None",
      "void",
      "void"
    ),
    tests: [
      { input: '["h","e","l","l","o"]', output: '["o","l","l","e","h"]', sample: true },
      { input: '["H","a","n","n","a","h"]', output: '["h","a","n","n","a","H"]', sample: true },
    ],
  },
  {
    id: "binary-search",
    slug: "binary-search",
    title: "Binary Search",
    difficulty: "Easy",
    tags: ["Array", "Binary Search"],
    published: true,
    languages: ["python", "cpp", "java"],
    description:
      "Given an array of integers nums which is sorted in ascending order, and an integer target, write a function to search target in nums. If target exists, return its index. Otherwise, return -1.\n\nYou must write an algorithm with O(log n) runtime complexity.",
    inputFormat: "nums: sorted integer array\ntarget: integer",
    outputFormat: "Index of target, or -1.",
    examples: [
      { input: "nums = [-1,0,3,5,9,12], target = 9", output: "4" },
      { input: "nums = [-1,0,3,5,9,12], target = 2", output: "-1" },
    ],
    constraints: [
      "1 <= nums.length <= 10^4",
      "-10^4 < nums[i], target < 10^4",
      "All integers in nums are unique.",
      "nums is sorted in ascending order.",
    ],
    starter: starter(
      "search",
      ", nums: List[int], target: int",
      "vector<int>& nums, int target",
      "int[] nums, int target",
      "int",
      "int",
      "int"
    ),
    tests: [
      { input: "[-1,0,3,5,9,12]\n9", output: "4", sample: true },
      { input: "[-1,0,3,5,9,12]\n2", output: "-1", sample: true },
    ],
  },
  {
    id: "valid-parentheses",
    slug: "valid-parentheses",
    title: "Valid Parentheses",
    difficulty: "Easy",
    tags: ["Stack", "String"],
    published: true,
    languages: ["python", "cpp", "java"],
    description:
      "Given a string s containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid.\n\nAn input string is valid if open brackets are closed by the same type of brackets, in the correct order, and every close bracket has a corresponding open bracket of the same type.",
    inputFormat: "s: string",
    outputFormat: "true or false",
    examples: [
      { input: 's = "()"', output: "true" },
      { input: 's = "()[]{}"', output: "true" },
      { input: 's = "(]"', output: "false" },
    ],
    constraints: ["1 <= s.length <= 10^4", "s consists of parentheses only: ()[]{}."],
    starter: starter(
      "isValid",
      ", s: str",
      "string s",
      "String s",
      "bool",
      "bool",
      "boolean"
    ),
    tests: [
      { input: "()", output: "true", sample: true },
      { input: "()[]{}", output: "true", sample: true },
      { input: "(]", output: "false", sample: true },
    ],
  },
  {
    id: "merge-intervals",
    slug: "merge-intervals",
    title: "Merge Intervals",
    difficulty: "Medium",
    tags: ["Array", "Sorting"],
    published: true,
    languages: ["python", "cpp", "java"],
    description:
      "Given an array of intervals where intervals[i] = [starti, endi], merge all overlapping intervals, and return an array of the non-overlapping intervals that cover all the intervals in the input.",
    inputFormat: "intervals: list of [start, end] pairs",
    outputFormat: "Merged list of intervals.",
    examples: [
      {
        input: "intervals = [[1,3],[2,6],[8,10],[15,18]]",
        output: "[[1,6],[8,10],[15,18]]",
        explanation: "[1,3] and [2,6] overlap.",
      },
      { input: "intervals = [[1,4],[4,5]]", output: "[[1,5]]" },
    ],
    constraints: ["1 <= intervals.length <= 10^4", "intervals[i].length == 2", "0 <= starti <= endi <= 10^4"],
    starter: starter(
      "merge",
      ", intervals: List[List[int]]",
      "vector<vector<int>>& intervals",
      "int[][] intervals",
      "List[List[int]]",
      "vector<vector<int>>",
      "int[][]"
    ),
    tests: [
      { input: "[[1,3],[2,6],[8,10],[15,18]]", output: "[[1,6],[8,10],[15,18]]", sample: true },
      { input: "[[1,4],[4,5]]", output: "[[1,5]]", sample: true },
    ],
  },
  {
    id: "longest-substring",
    slug: "longest-substring",
    title: "Longest Substring Without Repeating Characters",
    difficulty: "Medium",
    tags: ["Hash Table", "String", "Sliding Window"],
    published: true,
    languages: ["python", "cpp", "java"],
    description:
      "Given a string s, find the length of the longest substring without repeating characters.",
    inputFormat: "s: string",
    outputFormat: "Integer length.",
    examples: [
      { input: 's = "abcabcbb"', output: "3", explanation: 'The answer is "abc".' },
      { input: 's = "bbbbb"', output: "1" },
      { input: 's = "pwwkew"', output: "3", explanation: 'The answer is "wke".' },
    ],
    constraints: ["0 <= s.length <= 5 * 10^4", "s consists of English letters, digits, symbols and spaces."],
    starter: starter(
      "lengthOfLongestSubstring",
      ", s: str",
      "string s",
      "String s",
      "int",
      "int",
      "int"
    ),
    tests: [
      { input: "abcabcbb", output: "3", sample: true },
      { input: "bbbbb", output: "1", sample: true },
    ],
  },
  {
    id: "number-of-islands",
    slug: "number-of-islands",
    title: "Number of Islands",
    difficulty: "Medium",
    tags: ["DFS", "BFS", "Matrix"],
    published: true,
    languages: ["python", "cpp", "java"],
    description:
      'Given an m x n 2D binary grid which represents a map of \'1\'s (land) and \'0\'s (water), return the number of islands.\n\nAn island is surrounded by water and is formed by connecting adjacent lands horizontally or vertically. You may assume all four edges of the grid are all surrounded by water.',
    inputFormat: "grid: 2D array of '1' and '0'",
    outputFormat: "Integer count of islands.",
    examples: [
      {
        input: 'grid = [["1","1","1","1","0"],["1","1","0","1","0"],["1","1","0","0","0"],["0","0","0","0","0"]]',
        output: "1",
      },
      {
        input: 'grid = [["1","1","0","0","0"],["1","1","0","0","0"],["0","0","1","0","0"],["0","0","0","1","1"]]',
        output: "3",
      },
    ],
    constraints: ["m == grid.length", "n == grid[i].length", "1 <= m, n <= 300", "grid[i][j] is '0' or '1'."],
    starter: starter(
      "numIslands",
      ", grid: List[List[str]]",
      "vector<vector<char>>& grid",
      "char[][] grid",
      "int",
      "int",
      "int"
    ),
    tests: [
      {
        input: '[["1","1","0"],["1","1","0"],["0","0","1"]]',
        output: "2",
        sample: true,
      },
    ],
  },
  {
    id: "climbing-stairs",
    slug: "climbing-stairs",
    title: "Climbing Stairs",
    difficulty: "Easy",
    tags: ["Dynamic Programming"],
    published: true,
    languages: ["python", "cpp", "java"],
    description:
      "You are climbing a staircase. It takes n steps to reach the top. Each time you can either climb 1 or 2 steps. In how many distinct ways can you climb to the top?",
    inputFormat: "n: integer",
    outputFormat: "Number of distinct ways.",
    examples: [
      { input: "n = 2", output: "2", explanation: "1+1 or 2." },
      { input: "n = 3", output: "3" },
    ],
    constraints: ["1 <= n <= 45"],
    starter: starter("climbStairs", ", n: int", "int n", "int n", "int", "int", "int"),
    tests: [
      { input: "2", output: "2", sample: true },
      { input: "3", output: "3", sample: true },
    ],
  },
  {
    id: "maximum-subarray",
    slug: "maximum-subarray",
    title: "Maximum Subarray",
    difficulty: "Medium",
    tags: ["Array", "Dynamic Programming"],
    published: true,
    languages: ["python", "cpp", "java"],
    description:
      "Given an integer array nums, find the subarray with the largest sum, and return its sum.",
    inputFormat: "nums: integer array",
    outputFormat: "Integer maximum subarray sum.",
    examples: [
      {
        input: "nums = [-2,1,-3,4,-1,2,1,-5,4]",
        output: "6",
        explanation: "[4,-1,2,1] has the largest sum 6.",
      },
      { input: "nums = [1]", output: "1" },
      { input: "nums = [5,4,-1,7,8]", output: "23" },
    ],
    constraints: ["1 <= nums.length <= 10^5", "-10^4 <= nums[i] <= 10^4"],
    starter: starter(
      "maxSubArray",
      ", nums: List[int]",
      "vector<int>& nums",
      "int[] nums",
      "int",
      "int",
      "int"
    ),
    tests: [
      { input: "[-2,1,-3,4,-1,2,1,-5,4]", output: "6", sample: true },
      { input: "[1]", output: "1", sample: true },
    ],
  },
  {
    id: "lru-cache",
    slug: "lru-cache",
    title: "LRU Cache",
    difficulty: "Medium",
    tags: ["Hash Table", "Linked List", "Design"],
    published: true,
    languages: ["python", "cpp", "java"],
    description:
      "Design a data structure that follows the constraints of a Least Recently Used (LRU) cache.\n\nImplement LRUCache:\n- LRUCache(int capacity) initialize the cache with positive size capacity.\n- int get(int key) return the value of the key if it exists, otherwise return -1.\n- void put(int key, int value) update or insert the value. If the number of keys exceeds capacity, evict the least recently used key.\n\nThe functions get and put must each run in O(1) average time complexity.",
    inputFormat: "Sequence of constructor, get, and put operations.",
    outputFormat: "List of results for get operations (put returns null).",
    examples: [
      {
        input:
          '["LRUCache","put","put","get","put","get","put","get","get","get"]\n[[2],[1,1],[2,2],[1],[3,3],[2],[4,4],[1],[3],[4]]',
        output: "[null,null,null,1,null,-1,null,-1,3,4]",
      },
    ],
    constraints: ["1 <= capacity <= 3000", "0 <= key <= 10^4", "0 <= value <= 10^5", "At most 2 * 10^5 calls to get and put."],
    starter: {
      python: `class LRUCache:
    def __init__(self, capacity: int):
        pass

    def get(self, key: int) -> int:
        pass

    def put(self, key: int, value: int) -> None:
        pass
`,
      cpp: `#include <bits/stdc++.h>
using namespace std;

class LRUCache {
public:
    LRUCache(int capacity) {}
    int get(int key) { return -1; }
    void put(int key, int value) {}
};
`,
      java: `import java.util.*;

class LRUCache {
    public LRUCache(int capacity) {}
    public int get(int key) { return -1; }
    public void put(int key, int value) {}
}
`,
    },
    tests: [
      {
        input: "capacity=2; put(1,1); put(2,2); get(1); put(3,3); get(2)",
        output: "1,-1",
        sample: true,
      },
    ],
  },
  {
    id: "word-search",
    slug: "word-search",
    title: "Word Search",
    difficulty: "Medium",
    tags: ["Array", "Backtracking", "Matrix"],
    published: true,
    languages: ["python", "cpp", "java"],
    description:
      "Given an m x n grid of characters board and a string word, return true if word exists in the grid.\n\nThe word can be constructed from letters of sequentially adjacent cells, where adjacent cells are horizontally or vertically neighboring. The same letter cell may not be used more than once.",
    inputFormat: "board: 2D character grid\nword: string",
    outputFormat: "true or false",
    examples: [
      {
        input: 'board = [["A","B","C","E"],["S","F","C","S"],["A","D","E","E"]], word = "ABCCED"',
        output: "true",
      },
      {
        input: 'board = [["A","B","C","E"],["S","F","C","S"],["A","D","E","E"]], word = "SEE"',
        output: "true",
      },
      {
        input: 'board = [["A","B","C","E"],["S","F","C","S"],["A","D","E","E"]], word = "ABCB"',
        output: "false",
      },
    ],
    constraints: [
      "m == board.length",
      "n == board[i].length",
      "1 <= m, n <= 6",
      "1 <= word.length <= 15",
    ],
    starter: starter(
      "exist",
      ", board: List[List[str]], word: str",
      "vector<vector<char>>& board, string word",
      "char[][] board, String word",
      "bool",
      "bool",
      "boolean"
    ),
    tests: [
      {
        input: '[["A","B"],["C","D"]]\nABDC',
        output: "true",
        sample: true,
      },
    ],
  },
  {
    id: "trapping-rain-water",
    slug: "trapping-rain-water",
    title: "Trapping Rain Water",
    difficulty: "Hard",
    tags: ["Array", "Two Pointers", "Stack"],
    published: true,
    languages: ["python", "cpp", "java"],
    description:
      "Given n non-negative integers representing an elevation map where the width of each bar is 1, compute how much water it can trap after raining.",
    inputFormat: "height: integer array",
    outputFormat: "Integer units of trapped water.",
    examples: [
      { input: "height = [0,1,0,2,1,0,1,3,2,1,2,1]", output: "6" },
      { input: "height = [4,2,0,3,2,5]", output: "9" },
    ],
    constraints: ["n == height.length", "1 <= n <= 2 * 10^4", "0 <= height[i] <= 10^5"],
    starter: starter(
      "trap",
      ", height: List[int]",
      "vector<int>& height",
      "int[] height",
      "int",
      "int",
      "int"
    ),
    tests: [
      { input: "[0,1,0,2,1,0,1,3,2,1,2,1]", output: "6", sample: true },
      { input: "[4,2,0,3,2,5]", output: "9", sample: true },
    ],
  },
  {
    id: "median-sorted-arrays",
    slug: "median-sorted-arrays",
    title: "Median of Two Sorted Arrays",
    difficulty: "Hard",
    tags: ["Array", "Binary Search"],
    published: true,
    languages: ["python", "cpp", "java"],
    description:
      "Given two sorted arrays nums1 and nums2 of size m and n respectively, return the median of the two sorted arrays.\n\nThe overall run time complexity should be O(log (m+n)).",
    inputFormat: "nums1, nums2: sorted integer arrays",
    outputFormat: "Median as a float.",
    examples: [
      { input: "nums1 = [1,3], nums2 = [2]", output: "2.00000" },
      { input: "nums1 = [1,2], nums2 = [3,4]", output: "2.50000" },
    ],
    constraints: [
      "nums1.length == m",
      "nums2.length == n",
      "0 <= m <= 1000",
      "0 <= n <= 1000",
      "1 <= m + n <= 2000",
    ],
    starter: starter(
      "findMedianSortedArrays",
      ", nums1: List[int], nums2: List[int]",
      "vector<int>& nums1, vector<int>& nums2",
      "int[] nums1, int[] nums2",
      "float",
      "double",
      "double"
    ),
    tests: [
      { input: "[1,3]\n[2]", output: "2.00000", sample: true },
      { input: "[1,2]\n[3,4]", output: "2.50000", sample: true },
    ],
  },
  {
    id: "course-schedule",
    slug: "course-schedule",
    title: "Course Schedule",
    difficulty: "Medium",
    tags: ["Graph", "DFS", "BFS", "Topological Sort"],
    published: true,
    languages: ["python", "cpp", "java"],
    description:
      "There are a total of numCourses courses you have to take, labeled from 0 to numCourses - 1. You are given an array prerequisites where prerequisites[i] = [ai, bi] indicates that you must take course bi first if you want to take course ai.\n\nReturn true if you can finish all courses. Otherwise, return false.",
    inputFormat: "numCourses: integer\nprerequisites: list of [ai, bi]",
    outputFormat: "true or false",
    examples: [
      { input: "numCourses = 2, prerequisites = [[1,0]]", output: "true" },
      { input: "numCourses = 2, prerequisites = [[1,0],[0,1]]", output: "false" },
    ],
    constraints: [
      "1 <= numCourses <= 2000",
      "0 <= prerequisites.length <= 5000",
      "prerequisites[i].length == 2",
    ],
    starter: starter(
      "canFinish",
      ", numCourses: int, prerequisites: List[List[int]]",
      "int numCourses, vector<vector<int>>& prerequisites",
      "int numCourses, int[][] prerequisites",
      "bool",
      "bool",
      "boolean"
    ),
    tests: [
      { input: "2\n[[1,0]]", output: "true", sample: true },
      { input: "2\n[[1,0],[0,1]]", output: "false", sample: true },
    ],
  },
  {
    id: "kth-largest",
    slug: "kth-largest",
    title: "Kth Largest Element in an Array",
    difficulty: "Medium",
    tags: ["Heap", "Sorting", "Array"],
    published: false,
    languages: ["python", "cpp", "java"],
    description:
      "Given an integer array nums and an integer k, return the kth largest element in the array.\n\nNote that it is the kth largest element in the sorted order, not the kth distinct element. You must solve it in O(n) time complexity for full credit.",
    inputFormat: "nums: integer array\nk: integer",
    outputFormat: "The kth largest integer.",
    examples: [
      { input: "nums = [3,2,1,5,6,4], k = 2", output: "5" },
      { input: "nums = [3,2,3,1,2,4,5,5,6], k = 4", output: "4" },
    ],
    constraints: ["1 <= k <= nums.length <= 10^5", "-10^4 <= nums[i] <= 10^4"],
    starter: starter(
      "findKthLargest",
      ", nums: List[int], k: int",
      "vector<int>& nums, int k",
      "int[] nums, int k",
      "int",
      "int",
      "int"
    ),
    tests: [
      { input: "[3,2,1,5,6,4]\n2", output: "5", sample: true },
    ],
  },
];
