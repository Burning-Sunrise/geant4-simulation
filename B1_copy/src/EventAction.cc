//
// ********************************************************************
// * License and Disclaimer                                           *
// *                                                                  *
// * The  Geant4 software  is  copyright of the Copyright Holders  of *
// * the Geant4 Collaboration.  It is provided  under  the terms  and *
// * conditions of the Geant4 Software License,  included in the file *
// * LICENSE and available at  http://cern.ch/geant4/license .  These *
// * include a list of copyright holders.                             *
// *                                                                  *
// * Neither the authors of this software system, nor their employing *
// * institutes,nor the agencies providing financial support for this *
// * work  make  any representation or  warranty, express or implied, *
// * regarding  this  software system or assume any liability for its *
// * use.  Please see the license in the file  LICENSE  and URL above *
// * for the full disclaimer and the limitation of liability.         *
// *                                                                  *
// * This  code  implementation is the result of  the  scientific and *
// * technical work of the GEANT4 collaboration.                      *
// * By using,  copying,  modifying or  distributing the software (or *
// * any work based  on the software)  you  agree  to acknowledge its *
// * use  in  resulting  scientific  publications,  and indicate your *
// * acceptance of all terms of the Geant4 Software license.          *
// ********************************************************************
//
//
/// \file B1/src/EventAction.cc
/// \brief Implementation of the B1::EventAction class

#include "EventAction.hh"

#include "RunAction.hh"

namespace B1
{

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

EventAction::EventAction(RunAction* runAction) {}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void EventAction::BeginOfEventAction(G4Event const*)
{
    // Reset all boundary state so a stopped/range-out event cannot inherit the
    // previous event's values.
    fEntered = false;
    fEntryPos = G4ThreeVector();
    fEntryMom = G4ThreeVector();
    fEntryKE = 0.;
    fExited = false;
    fPos = G4ThreeVector();
    fMom = G4ThreeVector();
    fKE = 0.;
    fGasTrackLength = 0.;
    fGasStepCount = 0;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void EventAction::EndOfEventAction(G4Event const* event)
{
    G4int eventID = event->GetEventID();

    // Persist non-zero energy-deposit hits when a hit collection exists.
    G4HCofThisEvent* hce = event->GetHCofThisEvent();
    TPCHitCollection* hitsCollection = nullptr;
    if (hce)
    {
        static G4int hcID = G4SDManager::GetSDMpointer()->GetCollectionID(
            "SD/TPCHitCollection");
        hitsCollection = static_cast<TPCHitCollection*>(hce->GetHC(hcID));
    }

    auto analysisManager = G4AnalysisManager::Instance();
    if (hitsCollection)
    {
        size_t nHits = hitsCollection->entries();
        for (size_t i = 0; i < nHits; i++)
        {
            TPCHit* hit = (*hitsCollection)[i];
            G4int pdgID = hit->GetPDGID();
            if (std::abs(pdgID) == 13 || pdgID == 2212)
            {
                analysisManager->FillNtupleIColumn(0, 0, eventID);
                analysisManager->FillNtupleDColumn(0, 1, hit->GetEdep());
                analysisManager->FillNtupleDColumn(0, 2, hit->GetPos().x());
                analysisManager->FillNtupleDColumn(0, 3, hit->GetPos().y());
                analysisManager->FillNtupleDColumn(0, 4, hit->GetPos().z());
                analysisManager->AddNtupleRow(0);
            }
        }
    }

    // Write exactly one boundary-state row for each primary that exits.
    if (GetExited())
    {
        analysisManager->FillNtupleIColumn(1, 0, eventID);
        analysisManager->FillNtupleDColumn(1, 1, GetExitKE());
        analysisManager->FillNtupleDColumn(1, 2, GetExitMom().x());
        analysisManager->FillNtupleDColumn(1, 3, GetExitMom().y());
        analysisManager->FillNtupleDColumn(1, 4, GetExitMom().z());
        analysisManager->FillNtupleDColumn(1, 5, GetExitPos().x());
        analysisManager->FillNtupleDColumn(1, 6, GetExitPos().y());
        analysisManager->FillNtupleDColumn(1, 7, GetExitPos().z());
        analysisManager->FillNtupleDColumn(1, 8, GetEntryKE());
        analysisManager->FillNtupleDColumn(1, 9, GetEntryMom().x());
        analysisManager->FillNtupleDColumn(1, 10, GetEntryMom().y());
        analysisManager->FillNtupleDColumn(1, 11, GetEntryMom().z());
        analysisManager->FillNtupleDColumn(1, 12, GetEntryPos().x());
        analysisManager->FillNtupleDColumn(1, 13, GetEntryPos().y());
        analysisManager->FillNtupleDColumn(1, 14, GetEntryPos().z());
        analysisManager->FillNtupleDColumn(1, 15, GetGasTrackLength());
        analysisManager->FillNtupleIColumn(1, 16, GetGasStepCount());
        analysisManager->FillNtupleIColumn(1, 17, GetEntered() ? 1 : 0);
        analysisManager->AddNtupleRow(1);
    }
}
//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

}  // namespace B1
