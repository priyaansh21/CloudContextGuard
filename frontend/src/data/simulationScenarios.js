/**
 * Attack Simulation Lab scenario definitions.
 *
 * Each scenario only defines REQUEST INPUTS - the exact payload that gets
 * POSTed to /api/access/request. No decision, risk score, or pass/fail
 * value is stored here: the backend security engine is the sole authority
 * on the outcome. The simulator renders whatever the API actually returns.
 */

export const SCENARIOS = [
  {
    id: 'legitimate-developer',
    name: 'Legitimate Developer Access',
    threatLevel: 'LOW',
    description:
      'A developer accesses an internal project resource from the trusted development VPC with MFA enabled.',
    attackVector: 'N/A - baseline legitimate request for comparison',
    requestPayload: {
      user: 'developer01',
      action: 'GetObject',
      resource: 'project-data',
      source_ip: '10.10.1.25',
      source_vpc: 'vpc-development',
      mfa: true,
      request_type: 'NORMAL',
    },
  },
  {
    id: 'trusted-identity-untrusted-network',
    name: 'Trusted Identity, Untrusted Network',
    threatLevel: 'CRITICAL',
    description: 'An authorized storage identity attempts to access confidential data from outside its trusted VPC.',
    attackVector: 'Valid IAM-authorized identity operating from an untrusted external network without MFA',
    requestPayload: {
      user: 'contractor01',
      action: 'GetObject',
      resource: 'financial-records',
      source_ip: '185.22.91.11',
      source_vpc: 'external',
      mfa: false,
      request_type: 'SUSPICIOUS',
    },
  },
  {
    id: 'stolen-credential',
    name: 'Stolen Credential Attack',
    threatLevel: 'CRITICAL',
    description:
      'A valid developer identity is used from an untrusted external network to request a resource the role was never granted, without MFA.',
    attackVector: 'Compromised credentials replayed from an external network',
    requestPayload: {
      user: 'developer01',
      action: 'GetObject',
      resource: 'financial-records',
      source_ip: '185.22.91.11',
      source_vpc: 'external',
      mfa: false,
      request_type: 'SUSPICIOUS',
    },
  },
  {
    id: 'external-confidential-storage',
    name: 'External Confidential Storage Access',
    threatLevel: 'HIGH',
    description:
      'A user with valid IAM permission for a CONFIDENTIAL resource attempts access from outside the resource\'s trusted VPC boundary.',
    attackVector: 'Valid permission exercised from an untrusted network boundary',
    requestPayload: {
      user: 'finance01',
      action: 'GetObject',
      resource: 'financial-records',
      source_ip: '203.0.113.25',
      source_vpc: 'external',
      mfa: true,
      request_type: 'SUSPICIOUS',
    },
  },
  {
    id: 'repeated-unauthorized',
    name: 'Repeated Unauthorized Requests',
    threatLevel: 'HIGH',
    description:
      'The same identity submits multiple denied requests against a restricted resource within a short window, escalating risk via the backend\'s repeated-failure detection.',
    attackVector: 'Brute-force-style repeated authorization attempts',
    repeated: true,
    attempts: 3,
    requestPayload: {
      user: 'developer01',
      action: 'GetObject',
      resource: 'credentials-vault',
      source_ip: '10.10.1.25',
      source_vpc: 'vpc-development',
      mfa: true,
      request_type: 'SUSPICIOUS',
    },
  },
  {
    id: 'privilege-escalation',
    name: 'Privilege Escalation Attempt',
    threatLevel: 'CRITICAL',
    description:
      'A DeveloperRole identity attempts an administrative action on a RESTRICTED resource that its role was never granted permission for.',
    attackVector: 'Unauthorized privilege escalation via an unpermitted action',
    requestPayload: {
      user: 'developer01',
      action: 'DeleteObject',
      resource: 'credentials-vault',
      source_ip: '10.10.1.25',
      source_vpc: 'vpc-development',
      mfa: true,
      request_type: 'SUSPICIOUS',
    },
  },
]
