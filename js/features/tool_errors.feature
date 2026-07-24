Feature: Handling a missing allium installation gracefully

  As someone running run-allium in an environment without allium installed
  I want a clear, actionable error instead of a stack trace
  So I know exactly how to fix my setup

  Scenario: Checking a spec when allium isn't installed reports a helpful error
    Given allium is not installed
    And a spec file named "clean.allium" with:
      """
      -- allium: 1

      entity Widget {
          id: Integer
          status: idle | active
      }
      """
    When I run the CLI against "clean.allium"
    Then the CLI exits with status 2
    And stderr includes "could not run"
    And stderr includes "brew install"
