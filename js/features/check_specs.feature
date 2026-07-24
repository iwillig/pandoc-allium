Feature: Checking Allium specs from the command line

  As someone writing Allium specs in a JS-based toolchain
  I want run-allium to check them the same way the pandoc filter does
  So invalid specs are caught before they're published anywhere

  Scenario: A well-formed spec passes with no diagnostics
    Given a spec file named "clean.allium" with:
      """
      -- allium: 1

      entity Widget {
          id: Integer
          status: idle | active
      }

      rule Activate {
          when: w: Widget.status
          requires: w.status = idle and w.id > 0
          ensures: w.status = active
      }

      rule Deactivate {
          when: w: Widget.status
          requires: w.status = active
          ensures: w.status = idle
      }
      """
    When I run the CLI against "clean.allium"
    Then the CLI exits with status 0
    And the output reports "clean.allium: ok"

  Scenario: A spec referencing an undeclared type is reported as an error
    Given a spec file named "broken.allium" with:
      """
      entity Order {
          id: UUID
      }
      """
    When I run the CLI against "broken.allium"
    Then the CLI exits with status 1
    And the output includes an "error" diagnostic mentioning "UUID"

  Scenario: Checking multiple specs at once reports each one
    Given a spec file named "clean.allium" with:
      """
      -- allium: 1

      entity Widget {
          id: Integer
          status: idle | active
      }

      rule Activate {
          when: w: Widget.status
          requires: w.status = idle and w.id > 0
          ensures: w.status = active
      }

      rule Deactivate {
          when: w: Widget.status
          requires: w.status = active
          ensures: w.status = idle
      }
      """
    And a spec file named "broken.allium" with:
      """
      entity Order {
          id: UUID
      }
      """
    When I run the CLI against "clean.allium" and "broken.allium"
    Then the CLI exits with status 1
    And the output reports "clean.allium: ok"
    And the output includes an "error" diagnostic mentioning "UUID"

  Scenario: Running with no files prints usage instead of crashing
    When I run the CLI with no files
    Then the CLI exits with status 2
    And stderr includes "usage: run-allium"
