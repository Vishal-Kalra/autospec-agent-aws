# Generated Specification

## Requirement 1: Calculate tip amount
- **[1.1]** GIVEN a valid bill total and tip percentage WHEN the calculator is invoked THEN it returns tip_amount = bill * percentage / 100, rounded to 2 decimal places

## Requirement 2: Calculate total with tip
- **[2.1]** GIVEN a bill total and computed tip amount WHEN the calculator is invoked THEN it returns total_with_tip = bill + tip_amount, rounded to 2 decimal places

## Requirement 3: Split evenly per person
- **[3.1]** GIVEN a total_with_tip and number of people >= 1 WHEN the calculator is invoked THEN it returns per_person = total_with_tip / people, rounded to 2 decimal places

## Requirement 4: Zero tip allowed
- **[4.1]** GIVEN a tip percentage of 0 WHEN the calculator is invoked THEN it returns tip_amount=0.00 and total_with_tip equals the bill total

## Requirement 5: Reject invalid people count
- **[5.1]** GIVEN a number of people less than 1 or not an integer WHEN the calculator is invoked THEN it raises ValueError indicating people must be an integer >= 1

## Requirement 6: Reject negative inputs
- **[6.1]** GIVEN a bill total < 0 or tip percentage < 0 WHEN the calculator is invoked THEN it raises ValueError indicating the value is out of allowed range

## Edge Cases
- Bill of exactly 0.00 with any valid tip
- Tip percentage of 100% (doubles the bill)
- Very large bill (999,999,999.99)
- Single person (per_person equals total)
- Fractional splits requiring rounding
- Tip of 0% with multiple people