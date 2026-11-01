/** Demo client emails, copied from backend/samples. */

export interface Sample {
  label: string;
  text: string;
}

export const clientEmails: Sample[] = [
  { label: "Complete request", text: "From: Client A <client.a@companya.example>\nTo: Umar Azhar <umar.azhar@hotela.example>\nSubject: Sales kickoff 2027 - room block request\n\nHi Umar,\n\nI'm organising our annual sales kickoff for Company A and we'd love to bring the team to Lisbon.\nWe need rooms for 12-15 March 2027 (arrive Friday 12th, leave Monday 15th).\n\nRough numbers:\n- 40 Standard Kings each night\n- 10 Deluxe Kings each night\n- 3 Junior Suites on the Saturday night only, for our leadership team\n\nWe will also need a breakfast package for everybody, and a welcome reception for around 60 people on the Friday evening.\n\nCould you send me a proposal by the end of next week?\n\nThanks,\nClient A\nEvents Manager, Company A\nclient.a@companya.example | +44 20 7946 0123\n" },
  { label: "Dates missing", text: "From: Client B <client.b@companyb.example>\nTo: Umar Azhar <umar.azhar@hotela.example>\nSubject: Group enquiry - wedding party\n\nHello,\n\nI have a wedding party coming to Lisbon in the spring and need about 25 rooms, mostly doubles, and a few suites for the family.\nWhat do you have?\n\nClient B\nCompany B\n" },
  { label: "Relative dates", text: "From: Client C <client.c@companyc.example>\nTo: Umar Azhar <umar.azhar@hotela.example>\nSubject: Advisory board dinner + rooms\n\nUmar,\n\nCompany C is holding an advisory board meeting in Lisbon the first weekend of February 2027 (Thursday night to Sunday morning).\nWe expect 18 guests. Everyone gets their own room, so please quote 12 Standard Kings and 6 Deluxe Kings for all nights.\n\nPlease keep this confidential, and copy me at client.c@companyc.example on everything.\n\nAmara\nHead of Medical Affairs Events, Company C\n" },
];
