---
title: "PowerShell Arrays for Beginners"
date: 2025-06-01T23:00:00-04:00
categories:
  - powershell
  - scripting
tags:
  - arrays
  - beginners
  - automation
excerpt: "A quick walkthrough of PowerShell arrays for beginners. Learn how to declare, access, modify, and join array data in scripts or the console."
author_profile: true
read_time: true
share: true
related: true
toc: false
last_modified_at: 2025-06-01T23:00:00-04:00
---

In this short video, I walk through the fundamentals of working with **PowerShell arrays**. If you're just getting started, this is a great place to begin.

👉 **Watch here**: [PowerShell Arrays for Beginners](https://www.youtube.com/watch?v=sV77XsKhiP4)

### Topics Covered in the Video

- **Declare an empty array**

  ```powershell
  $myArray = @()
  ```

- **Populate the array with strings**

  ```powershell
  $myArray = "zero", "one", "two"
  ```

- **Access elements by index**

  - First element (`0`), last element (`-1`), or any position:

    ```powershell
    $myArray[0]      # zero
    $myArray[-1]     # two
    ```

- **Select multiple elements**

  ```powershell
  $myArray[0,2]      # zero and two
  $myArray[1..3]     # one, two, three
  ```

- **Add elements with `+=`**  
  _(recreates the array each time — fine for small lists)_

  ```powershell
  $myArray += "three"
  ```

- **Inspect the variable type**

  ```powershell
  $myArray.GetType()
  ```

- **List available members**

  ```powershell
  $myArray | Get-Member
  ```

- **Check array length**

  ```powershell
  $myArray.Length
  ```

- **Clear the array**

  ```powershell
  $myArray.Clear()
  ```

- **Review and reuse console history**

  ```powershell
  Get-History      # alias: h
  Invoke-History 3 # alias: r 3
  ```

- **Join array elements into a string**

  ```powershell
  $joined = $myArray -join ", "
  ```

- **Split a string back into an array**

  ```powershell
  $newArray = $joined -split ", "
  ```

Arrays are one of the most common and useful data structures you’ll use in PowerShell scripting—get to know them well. Thanks for watching!
